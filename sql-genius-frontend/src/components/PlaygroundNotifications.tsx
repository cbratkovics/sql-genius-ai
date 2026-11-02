'use client';

import { resolveValue, ToastIcon, useToaster } from 'react-hot-toast';

/** Keep the latest operation status beside the SQL controls, without an overlay. */
export default function PlaygroundNotifications() {
  const { toasts, handlers } = useToaster({ duration: 4000 });
  const latest = toasts.find(toast => toast.visible);

  return (
    <div
      role="status"
      aria-label="Playground notifications"
      aria-live="polite"
      aria-atomic="true"
      className="min-h-14"
      onMouseEnter={handlers.startPause}
      onMouseLeave={handlers.endPause}
    >
      {latest && (
        <div className="flex items-center gap-3 rounded-lg border border-gray-600 bg-gray-800 p-3 text-sm text-white">
          <span aria-hidden="true"><ToastIcon toast={latest} /></span>
          <span className="min-w-0 break-words">{resolveValue(latest.message, latest)}</span>
        </div>
      )}
    </div>
  );
}
