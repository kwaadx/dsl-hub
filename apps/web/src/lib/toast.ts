type ToastPayload = {
  summary?: string;
  detail: string;
  life?: number;
  severity?: 'info' | 'warn' | 'error' | 'success';
};

let showFn: ((p: ToastPayload) => void) | null = null;

export function registerToast(show: (p: ToastPayload) => void) {
  showFn = show;
}

export function toastError(detail: string, summary = 'Error') {
  showFn?.({severity: 'error', summary, detail, life: 6000});
}

export function toastSuccess(detail: string, summary = 'Success') {
  showFn?.({severity: 'success', summary, detail, life: 4000});
}

export function toastInfo(detail: string, summary = 'Info') {
  showFn?.({severity: 'info', summary, detail, life: 4000});
}

export function toastWarn(detail: string, summary = 'Warning') {
  showFn?.({severity: 'warn', summary, detail, life: 4000});
}
