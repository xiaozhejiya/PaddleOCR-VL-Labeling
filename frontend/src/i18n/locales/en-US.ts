export default {
  common: {
    save: 'Save',
    cancel: 'Cancel',
    confirm: 'Confirm',
    delete: 'Delete',
    edit: 'Edit',
    create: 'Create',
    search: 'Search',
    loading: 'Loading...',
    noData: 'No data',
    success: 'Success',
    error: 'Error',
    retry: 'Retry',
    back: 'Back',
  },
  auth: {
    login: 'Login',
    register: 'Register',
    logout: 'Logout',
    username: 'Username',
    password: 'Password',
    email: 'Email',
    forgotPassword: 'Forgot Password',
    noAccount: "Don't have an account?",
    hasAccount: 'Already have an account?',
  },
  project: {
    title: 'Projects',
    create: 'Create Project',
    name: 'Project Name',
    description: 'Description',
    status: 'Status',
    actions: 'Actions',
  },
  annotation: {
    saveStatus: {
      saved: 'Saved',
      saving: 'Saving...',
      dirty: 'Unsaved',
      conflict: 'Conflict',
      readonly: 'Read Only',
      autosave_pending: 'Auto-save Pending',
      autosaving: 'Auto-saving...',
      autosave_failed: 'Auto-save Failed',
      manual_saving: 'Saving...',
    },
  },
  workspace: {
    taskQueue: 'Task Queue',
    canvasPlaceholder: 'Annotation canvas in development...',
    propertiesPanel: 'Properties',
    revisionLog: 'Revision Log',
    leaveConfirm: 'You have unsaved changes. Are you sure you want to leave?',
  },
  // Route title i18n keys
  routes: {
    auth: {
      login: 'Login',
      register: 'Register',
    },
    app: {
      home: 'Workspace',
    },
    projects: {
      index: 'Projects',
      detail: 'Project Detail',
      tabs: {
        jobs: 'Jobs',
        exports: 'Exports',
      },
    },
    pages: {
      workspace: 'Annotation Workspace',
    },
    settings: {
      index: 'Settings',
    },
    error: {
      forbidden: 'Access Denied',
      notFound: 'Page Not Found',
    },
  },
  errors: {
    network: 'Network error, please check your connection',
    unauthorized: 'Not logged in, please login first',
    forbidden: 'Permission denied',
    notFound: 'Resource not found',
    server: 'Server error, please try again later',
    unknown: 'Unknown error',
  },
}
