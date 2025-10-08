export const le = (message: any, ...args: any[]): void => {
  console.error(message, ...args);
};

export const ll = (message: any, ...args: any[]): void => {
  console.log(message, ...args);
};

export const lw = (message: any, ...args: any[]): void => {
  console.warn(message, ...args);
};

declare global {
  interface Window {
    le: typeof le;
    ll: typeof ll;
    lw: typeof lw;
  }
}

if (typeof window !== 'undefined') {
  window.le = le;
  window.ll = ll;
  window.lw = lw;
}
