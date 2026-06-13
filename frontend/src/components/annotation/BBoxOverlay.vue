<script setup lang="ts">
/**
 * 单个标注框 SVG overlay
 * 渲染 bbox 矩形 + label badge + read_order + 选中时的 8 个控制点
 *
 * props.obj 接收视口坐标系下的对象（viewportBbox 已由 AnnotationCanvas 转换）
 */
import { computed } from 'vue'

interface ViewportObject {
  id: string
  type: string
  label_namespace: string
  viewportBbox: [number, number, number, number]
  read_order?: number
  color: string
  status: string
}

interface Props {
  obj: ViewportObject
  selected: boolean
  labelName: string
  activeTool: 'select' | 'bbox' | 'read_order' | 'pan'
}

const props = defineProps<Props>()

const emit = defineEmits<{
  select: []
  dragStart: [e: MouseEvent]
  handleDragStart: [handleIndex: number, e: MouseEvent]
}>()

const HANDLE_SIZE = 8

const x = computed(() => props.obj.viewportBbox[0])
const y = computed(() => props.obj.viewportBbox[1])
const w = computed(() => props.obj.viewportBbox[2] - props.obj.viewportBbox[0])
const h = computed(() => props.obj.viewportBbox[3] - props.obj.viewportBbox[1])

/** 8 个控制点位置：上中、右上、右中、右下、下中、左下、左中、左上 */
const handles = computed(() => {
  const [xmin, ymin, xmax, ymax] = props.obj.viewportBbox
  const cx = (xmin + xmax) / 2
  const cy = (ymin + ymax) / 2
  return [
    { x: cx, y: ymin, cursor: 'ns-resize', idx: 0 },     // 上中
    { x: xmax, y: ymin, cursor: 'nesw-resize', idx: 1 },  // 右上
    { x: xmax, y: cy, cursor: 'ew-resize', idx: 2 },      // 右中
    { x: xmax, y: ymax, cursor: 'nwse-resize', idx: 3 },  // 右下
    { x: cx, y: ymax, cursor: 'ns-resize', idx: 4 },      // 下中
    { x: xmin, y: ymax, cursor: 'nesw-resize', idx: 5 },  // 左下
    { x: xmin, y: cy, cursor: 'ew-resize', idx: 6 },      // 左中
    { x: xmin, y: ymin, cursor: 'nwse-resize', idx: 7 },  // 左上
  ]
})

function onRectMouseDown(e: MouseEvent) {
  emit('select')
  emit('dragStart', e)
}

function onHandleMouseDown(idx: number, e: MouseEvent) {
  emit('select')
  emit('handleDragStart', idx, e)
}
</script>

<template>
  <g :class="selected ? 'opacity-100' : 'opacity-80'">
    <!-- bbox 矩形 -->
    <rect
      :x="x"
      :y="y"
      :width="w"
      :height="h"
      :fill="selected ? `${obj.color}10` : 'transparent'"
      :stroke="obj.color"
      :stroke-width="selected ? 2 : 1.5"
      class="cursor-move"
      @mousedown.left="onRectMouseDown"
    />

    <!-- label badge -->
    <g :transform="`translate(${x}, ${y - 20})`">
      <rect
        :width="Math.max(labelName.length * 8 + 12, 40)"
        height="18"
        rx="3"
        :fill="obj.color"
      />
      <text
        x="6"
        y="13"
        fill="white"
        font-size="11"
        font-weight="500"
        font-family="Inter, sans-serif"
        pointer-events="none"
      >
        {{ labelName }}
      </text>
    </g>

    <!-- read_order badge -->
    <g v-if="obj.read_order && obj.read_order > 0" :transform="`translate(${x + w - 18}, ${y})`">
      <rect
        width="18"
        height="18"
        rx="9"
        :fill="obj.color"
        opacity="0.9"
      />
      <text
        x="9"
        y="13"
        fill="white"
        font-size="10"
        font-weight="600"
        text-anchor="middle"
        font-family="Inter, sans-serif"
        pointer-events="none"
      >
        {{ obj.read_order }}
      </text>
    </g>

    <!-- 选中时的控制点 -->
    <template v-if="selected && activeTool === 'select'">
      <rect
        v-for="handle in handles"
        :key="handle.idx"
        :x="handle.x - HANDLE_SIZE / 2"
        :y="handle.y - HANDLE_SIZE / 2"
        :width="HANDLE_SIZE"
        :height="HANDLE_SIZE"
        fill="white"
        :stroke="obj.color"
        stroke-width="1.5"
        :style="{ cursor: handle.cursor }"
        @mousedown.left.stop="onHandleMouseDown(handle.idx, $event)"
      />
    </template>
  </g>
</template>
