import { useEffect, useRef } from 'react';

const focusableSelector = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function useDialogFocus(dialogRef, onClose, preferredSelector) {
  const closeRef = useRef(onClose);
  useEffect(() => { closeRef.current = onClose; }, [onClose]);

  useEffect(() => {
    const previousFocus = document.activeElement;
    const dialog = dialogRef.current;
    const preferred = dialog?.querySelector(preferredSelector);
    (preferred || dialog)?.focus();
    return () => {
      if (previousFocus instanceof HTMLElement) previousFocus.focus();
    };
  }, [dialogRef, preferredSelector]);

  return (event) => {
    if (event.key === 'Escape') {
      event.preventDefault();
      closeRef.current?.();
      return;
    }
    if (event.key !== 'Tab') return;

    const dialog = event.currentTarget;
    const focusable = [...dialog.querySelectorAll(focusableSelector)].filter((element) => element.getClientRects().length > 0);
    if (!focusable.length) {
      event.preventDefault();
      dialog.focus();
      return;
    }

    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  };
}
