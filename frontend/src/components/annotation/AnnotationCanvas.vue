<script setup lang="ts">
/**
 * 标注画布组件
 * 图片 + SVG overlay + 鼠标交互
 */
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useCanvasTransform } from '@/composables/useCanvasTransform'
import { useAnnotationStore } from '@/composables/useAnnotationStore'
import BBoxOverlay from './BBoxOverlay.vue'

interface Props {
  imageUrl: string | null
  activeTool: 'select' | 'rectangle' | 'readingOrder' | 'pan'
  activeLabel: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:zoomLevel': [value: number]
  'object-selected': [id: string | null]
  'objects-changed': []
}>()

// ── 暴露 store 给父组件 ──
const store = useAnnotationStore()
const transform = useCanvasTransform()

defineExpose({ store, transform })

// ── 容器和图片引用 ──
const containerRef = ref<HTMLElement | null>(null)
const imageLoaded = ref(false)

// ── 鼠标交互状态 ──
const isDragging = ref(false)
const dragType = ref<'move' | 'resize' | 'draw' | 'pan' | null>(null)
const dragStartScreen = ref({ x: 0, y: 0 })
const dragStartImage = ref({ x: 0, y: 0 })
const dragHandleIndex = ref(0)
const dragObjectId = ref<string | null>(null)
const drawStartImage = ref({ x: 0, y: 0 })

// ── 画框临时矩形 ──
const tempRect = ref<{ x: number; y: number; w: number; h: number } | null>(null)

// ── 图片加载 ──
watch(() => props.imageUrl, (url) => {
  if (!url) return
  imageLoaded.value = false
  const img = new Image()
  img.onload = () => {
    transform.setImageSize(img.naturalWidth, img.naturalHeight)
    imageLoaded.value = true
    // 延迟到下一帧确保容器尺寸已更新
    requestAnimationFrame(() => {
      if (containerRef.value) {
        const w = containerRef.value.offsetWidth
        const h = containerRef.value.offsetHeight
        transform.setContainerSize(w, h)
        // 自适应容器大小，居中显示
        transform.fitToContainer()
        emit('update:zoomLevel', transform.zoomPercent.value)
      }
    })
  }
  img.src = url
}, { immediate: true })

// ── 容器尺寸监听 ──
let resizeObserver: ResizeObserver | null = null

onMounted(() => {
  if (containerRef.value) {
    transform.setContainerSize(containerRef.value.offsetWidth, containerRef.value.offsetHeight)
  }
  resizeObserver = new ResizeObserver((entries) => {
    const entry = entries[0]
    if (entry) {
      transform.setContainerSize(entry.contentRect.width, entry.contentRect.height)
    }
  })
  if (containerRef.value) {
    resizeObserver.observe(containerRef.value)
  }
})

onUnmounted(() => {
  resizeObserver?.disconnect()
})

// ── 滚轮缩放 ──
function onWheel(e: WheelEvent) {
  e.preventDefault()
  const delta = e.deltaY > 0 ? -0.1 : 0.1
  const rect = containerRef.value!.getBoundingClientRect()
  transform.zoom(delta, {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top,
  })
  emit('update:zoomLevel', transform.zoomPercent.value)
}

// ── 鼠标按下 ──
function onMouseDown(e: MouseEvent) {
  if (e.button !== 0) return

  const rect = containerRef.value!.getBoundingClientRect()
  const screenX = e.clientX - rect.left
  const screenY = e.clientY - rect.top
  const imgPt = transform.screenToImage(screenX, screenY)

  dragStartScreen.value = { x: screenX, y: screenY }
  dragStartImage.value = imgPt

  // Space 临时平移模式
  if (props.activeTool === 'pan' || spaceHeld.value) {
    isDragging.value = true
    dragType.value = 'pan'
    return
  }

  // 矩形工具：画新框
  if (props.activeTool === 'rectangle') {
    isDragging.value = true
    dragType.value = 'draw'
    drawStartImage.value = imgPt
    tempRect.value = { x: imgPt.x, y: imgPt.y, w: 0, h: 0 }
    return
  }

  // 选择工具：点击空白取消选中
  if (props.activeTool === 'select') {
    // 检查是否点击了某个对象（由 BBoxOverlay 的 mousedown 处理）
    // 如果没点到任何对象，取消选中
    store.select(null)
    emit('object-selected', null)
  }
}

// ── 鼠标移动 ──
function onMouseMove(e: MouseEvent) {
  if (!isDragging.value) return

  const rect = containerRef.value!.getBoundingClientRect()
  const screenX = e.clientX - rect.left
  const screenY = e.clientY - rect.top
  const imgPt = transform.screenToImage(screenX, screenY)

  if (dragType.value === 'pan') {
    const dx = screenX - dragStartScreen.value.x
    const dy = screenY - dragStartScreen.value.y
    transform.pan(dx, dy)
    dragStartScreen.value = { x: screenX, y: screenY }
    emit('update:zoomLevel', transform.zoomPercent.value)
    return
  }

  if (dragType.value === 'draw' && tempRect.value) {
    tempRect.value = {
      x: Math.min(drawStartImage.value.x, imgPt.x),
      y: Math.min(drawStartImage.value.y, imgPt.y),
      w: Math.abs(imgPt.x - drawStartImage.value.x),
      h: Math.abs(imgPt.y - drawStartImage.value.y),
    }
    return
  }

  if (dragType.value === 'move' && dragObjectId.value) {
    const dx = imgPt.x - dragStartImage.value.x
    const dy = imgPt.y - dragStartImage.value.y
    store.moveObject(dragObjectId.value, dx, dy)
    dragStartImage.value = imgPt
    emit('objects-changed')
    return
  }

  if (dragType.value === 'resize' && dragObjectId.value) {
    store.resizeObject(dragObjectId.value, dragHandleIndex.value, imgPt.x, imgPt.y)
    emit('objects-changed')
    return
  }
}

// ── 鼠标释放 ──
function onMouseUp() {
  if (dragType.value === 'draw' && tempRect.value) {
    const { x, y, w, h } = tempRect.value
    // 最小面积检查
    if (w > 5 && h > 5) {
      store.addObject([x, y, x + w, y + h], props.activeLabel)
      emit('objects-changed')
    }
    tempRect.value = null
  }

  isDragging.value = false
  dragType.value = null
  dragObjectId.value = null
}

// ── BBox 事件处理 ──
function onBBoxSelect(id: string) {
  store.select(id)
  emit('object-selected', id)

  // readingOrder 模式：点击设置阅读顺序
  if (props.activeTool === 'readingOrder') {
    const maxOrder = store.objects.value.reduce((max, o) => Math.max(max, o.read_order), 0)
    store.setReadOrder(id, maxOrder + 1)
    emit('objects-changed')
  }
}

function onBBoxDragStart(id: string, e: MouseEvent) {
  if (props.activeTool !== 'select') return
  e.stopPropagation()

  const rect = containerRef.value!.getBoundingClientRect()
  const screenX = e.clientX - rect.left
  const screenY = e.clientY - rect.top
  const imgPt = transform.screenToImage(screenX, screenY)

  store.savePreDragSnapshot()
  isDragging.value = true
  dragType.value = 'move'
  dragObjectId.value = id
  dragStartImage.value = imgPt
}

function onBBoxHandleDragStart(id: string, handleIndex: number, e: MouseEvent) {
  e.stopPropagation()
  store.savePreDragSnapshot()
  isDragging.value = true
  dragType.value = 'resize'
  dragObjectId.value = id
  dragHandleIndex.value = handleIndex
}

// ── 键盘快捷键 ──
const spaceHeld = ref(false)

function onKeyDown(e: KeyboardEvent) {
  if (e.key === ' ') {
    e.preventDefault()
    spaceHeld.value = true
  }
  if (e.key === 'Delete' || e.key === 'Backspace') {
    if (store.selectedId.value) {
      store.deleteSelected()
      emit('objects-changed')
    }
  }
  if (e.ctrlKey && e.key === 'z') {
    e.preventDefault()
    store.undo()
    emit('objects-changed')
  }
  if (e.ctrlKey && e.key === 'y') {
    e.preventDefault()
    store.redo()
    emit('objects-changed')
  }
}

function onKeyUp(e: KeyboardEvent) {
  if (e.key === ' ') {
    spaceHeld.value = false
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('keyup', onKeyUp)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('keyup', onKeyUp)
})

// ── SVG viewBox ──
const svgViewBox = computed(() =>
  `0 0 ${transform.imageSize.value.x} ${transform.imageSize.value.y}`
)

// ── 光标样式 ──
const cursorClass = computed(() => {
  if (spaceHeld.value || props.activeTool === 'pan') return 'cursor-grab'
  if (props.activeTool === 'rectangle') return 'cursor-crosshair'
  if (props.activeTool === 'readingOrder') return 'cursor-pointer'
  return 'cursor-default'
})
</script>

<template>
  <div
    ref="containerRef"
    :class="['relative w-full h-full overflow-hidden bg-bg-canvas select-none', cursorClass]"
    @wheel.prevent="onWheel"
    @mousedown.left="onMouseDown"
    @mousemove="onMouseMove"
    @mouseup.left="onMouseUp"
    @mouseleave="onMouseUp"
  >
    <!-- 加载中 -->
    <div v-if="!imageLoaded" class="absolute inset-0 flex items-center justify-center text-text-muted">
      <div class="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
    </div>

    <!-- 图片 + SVG 层 -->
    <div
      v-show="imageLoaded"
      class="absolute top-0 left-0 origin-top-left pointer-events-none"
      :style="{ transform: transform.transformStyle.value }"
    >
      <!-- 页面图片 -->
      <img
        v-if="imageUrl"
        ref="imageRef"
        :src="imageUrl"
        class="block"
        :style="{ width: `${transform.imageSize.value.x}px`, height: `${transform.imageSize.value.y}px` }"
        draggable="false"
        @load="imageLoaded = true"
      />

      <!-- SVG overlay -->
      <svg
        class="absolute top-0 left-0 pointer-events-auto"
        :width="transform.imageSize.value.x"
        :height="transform.imageSize.value.y"
        :viewBox="svgViewBox"
        xmlns="http://www.w3.org/2000/svg"
      >
        <!-- 已有标注对象 -->
        <BBoxOverlay
          v-for="obj in store.objects.value"
          :key="obj.id"
          :obj="obj"
          :selected="store.selectedId.value === obj.id"
          :label-name="obj.label"
          @select="onBBoxSelect(obj.id)"
          @drag-start="(e) => onBBoxDragStart(obj.id, e)"
          @handle-drag-start="(idx, e) => onBBoxHandleDragStart(obj.id, idx, e)"
        />

        <!-- 画框临时矩形 -->
        <rect
          v-if="tempRect"
          :x="tempRect.x"
          :y="tempRect.y"
          :width="tempRect.w"
          :height="tempRect.h"
          fill="rgba(94, 106, 210, 0.1)"
          stroke="#5e6ad2"
          stroke-width="2"
          stroke-dasharray="6 3"
          pointer-events="none"
        />
      </svg>
    </div>
  </div>
</template>
