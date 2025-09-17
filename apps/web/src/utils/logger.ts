/**
 * Logger utility functions
 *
 * These functions provide a consistent way to log messages in the application.
 * They are used in main.ts and are attached to the window object for global access.
 */

/**
 * Log an error message to the console
 * @param message - The message to log
 * @param args - Additional arguments to log
 */
export const le = (message: any, ...args: any[]): void => {
  console.error(message, ...args);
};

/**
 * Log an info message to the console
 * @param message - The message to log
 * @param args - Additional arguments to log
 */
export const ll = (message: any, ...args: any[]): void => {
  console.log(message, ...args);
};

/**
 * Log a warning message to the console
 * @param message - The message to log
 * @param args - Additional arguments to log
 */
export const lw = (message: any, ...args: any[]): void => {
  console.warn(message, ...args);
};

// Add type declarations for the window object
declare global {
  interface Window {
    le: typeof le;
    ll: typeof ll;
    lw: typeof lw;
  }
}

// Assign logger functions to window object if in browser environment
if (typeof window !== 'undefined') {
  window.le = le;
  window.ll = ll;
  window.lw = lw;
}
