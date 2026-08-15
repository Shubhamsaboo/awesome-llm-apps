"use client";

import { useState, useCallback, useEffect } from "react";

const noop = () => {};

/**
 * Persist state in localStorage with JSON serialization.
 * SSR-safe: returns initial value until mounted.
 * Use this only for persistence (page reload). For shared state between
 * components, use React Context instead.
 */
export function useLocalStorage<T>(
  key: string,
  initialValue: T,
): [T, (value: T | ((prev: T) => T)) => void] {
  const [stored, setStored] = useState<T>(initialValue);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted || typeof window === "undefined") return;
    try {
      const raw = window.localStorage.getItem(key);
      if (raw != null) {
        setStored(JSON.parse(raw) as T);
      }
    } catch {
      noop();
    }
  }, [key, mounted]);

  const setValue = useCallback(
    (value: T | ((prev: T) => T)) => {
      setStored((prev: T) => {
        const next =
          typeof value === "function" ? (value as (p: T) => T)(prev) : value;
        if (typeof window !== "undefined") {
          try {
            window.localStorage.setItem(key, JSON.stringify(next));
          } catch {
            noop();
          }
        }
        return next;
      });
    },
    [key],
  );

  return [stored, setValue];
}
