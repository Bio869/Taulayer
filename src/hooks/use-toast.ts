// src/hooks/use-toast.ts
import * as React from "react";
import type { ToastActionElement, ToastProps } from "@/components/ui/toast";

const TOAST_LIMIT = 1;             // adjust if you want to allow more concurrent toasts
const TOAST_REMOVE_DELAY = 5000;   // default auto-remove (ms). Can be overridden per toast via `duration`

type ToasterToast = ToastProps & {
  id: string;
  title?: React.ReactNode;
  description?: React.ReactNode;
  action?: ToastActionElement;
  duration?: number;               // optional per-toast override for auto-remove delay
};

const actionTypes = {
  ADD_TOAST: "ADD_TOAST",
  UPDATE_TOAST: "UPDATE_TOAST",
  DISMISS_TOAST: "DISMISS_TOAST",
  REMOVE_TOAST: "REMOVE_TOAST",
} as const;

type Action =
  | { type: typeof actionTypes.ADD_TOAST; toast: ToasterToast }
  | { type: typeof actionTypes.UPDATE_TOAST; toast: Partial<ToasterToast> & { id: string } }
  | { type: typeof actionTypes.DISMISS_TOAST; toastId?: ToasterToast["id"] }
  | { type: typeof actionTypes.REMOVE_TOAST; toastId?: ToasterToast["id"] };

interface State {
  toasts: ToasterToast[];
}

let count = 0;
function genId() {
  count = (count + 1) % Number.MAX_SAFE_INTEGER;
  return count.toString();
}

const toastTimeouts = new Map<string, ReturnType<typeof setTimeout>>();

function clearFromQueue(id?: string) {
  if (!id) return;
  const t = toastTimeouts.get(id);
  if (t) clearTimeout(t);
  toastTimeouts.delete(id);
}

function addToRemoveQueue(toast: ToasterToast) {
  if (toastTimeouts.has(toast.id)) return;
  const timeout = setTimeout(() => {
    toastTimeouts.delete(toast.id);
    dispatch({ type: actionTypes.REMOVE_TOAST, toastId: toast.id });
  }, toast.duration ?? TOAST_REMOVE_DELAY);
  toastTimeouts.set(toast.id, timeout);
}

export const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case actionTypes.ADD_TOAST: {
      return {
        ...state,
        toasts: [action.toast, ...state.toasts].slice(0, TOAST_LIMIT),
      };
    }

    case actionTypes.UPDATE_TOAST: {
      return {
        ...state,
        toasts: state.toasts.map((t) => (t.id === action.toast.id ? { ...t, ...action.toast } : t)),
      };
    }

    case actionTypes.DISMISS_TOAST: {
      const { toastId } = action;

      if (toastId) {
        const t = state.toasts.find((x) => x.id === toastId);
        if (t) addToRemoveQueue(t);
      } else {
        state.toasts.forEach(addToRemoveQueue);
      }

      return {
        ...state,
        toasts: state.toasts.map((t) =>
          toastId === undefined || t.id === toastId ? { ...t, open: false } : t
        ),
      };
    }

    case actionTypes.REMOVE_TOAST: {
      if (action.toastId === undefined) {
        // remove all
        state.toasts.forEach((t) => clearFromQueue(t.id));
        return { ...state, toasts: [] };
      }
      clearFromQueue(action.toastId);
      return { ...state, toasts: state.toasts.filter((t) => t.id !== action.toastId) };
    }
  }
};

const listeners: Array<(state: State) => void> = [];
let memoryState: State = { toasts: [] };

function dispatch(action: Action) {
  memoryState = reducer(memoryState, action);
  listeners.forEach((listener) => listener(memoryState));
}

type Toast = Omit<ToasterToast, "id">;

function toast(props: Toast) {
  const id = genId();

  const update = (patch: Partial<ToasterToast>) =>
    dispatch({ type: actionTypes.UPDATE_TOAST, toast: { ...patch, id } });

  const dismiss = () => dispatch({ type: actionTypes.DISMISS_TOAST, toastId: id });

  dispatch({
    type: actionTypes.ADD_TOAST,
    toast: {
      ...props,
      id,
      open: true,
      onOpenChange: (open) => {
        if (!open) dismiss();
      },
    },
  });

  return { id, dismiss, update };
}

function useToast() {
  const [state, setState] = React.useState<State>(memoryState);

  React.useEffect(() => {
    listeners.push(setState);
    return () => {
      const index = listeners.indexOf(setState);
      if (index > -1) listeners.splice(index, 1);
    };
  }, []); // subscribe once

  return {
    ...state,
    toast,
    dismiss: (toastId?: string) => dispatch({ type: actionTypes.DISMISS_TOAST, toastId }),
  };
}

export { useToast, toast };
