import { computed, ref } from "vue";

export interface PendingOfflineAction {
  id?: string;
  type: string;
  payload: unknown;
  created_at?: string;
}

export interface OfflineFlushResult {
  synced: number;
  failed: number;
}

const DB_NAME = "xuexibao-offline";
const STORE_NAME = "pending_actions";
const LOCAL_STORAGE_KEY = "xuexibao:pending-actions";

const pendingCount = ref(0);
const online = ref(typeof navigator === "undefined" ? true : navigator.onLine);

function createAction(action: PendingOfflineAction): Required<PendingOfflineAction> {
  return {
    id: action.id || `${Date.now()}-${Math.random().toString(36).slice(2)}`,
    type: action.type,
    payload: action.payload,
    created_at: action.created_at || new Date().toISOString(),
  };
}

function hasIndexedDB() {
  return typeof indexedDB !== "undefined";
}

function openDB(): Promise<IDBDatabase | null> {
  if (!hasIndexedDB()) return Promise.resolve(null);

  return new Promise((resolve) => {
    const request = indexedDB.open(DB_NAME, 1);

    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: "id" });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => resolve(null);
  });
}

async function withStore<T>(
  mode: IDBTransactionMode,
  callback: (store: IDBObjectStore) => IDBRequest<T> | void,
): Promise<T | undefined> {
  const db = await openDB();
  if (!db) return undefined;

  return new Promise((resolve, reject) => {
    const transaction = db.transaction(STORE_NAME, mode);
    const store = transaction.objectStore(STORE_NAME);
    const request = callback(store);

    if (!request) {
      transaction.oncomplete = () => resolve(undefined);
      transaction.onerror = () => reject(transaction.error);
      return;
    }

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

function readFallback(): Required<PendingOfflineAction>[] {
  try {
    return JSON.parse(localStorage.getItem(LOCAL_STORAGE_KEY) || "[]");
  } catch {
    return [];
  }
}

function writeFallback(actions: Required<PendingOfflineAction>[]) {
  localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(actions));
  pendingCount.value = actions.length;
}

async function refreshPendingCount() {
  const actions = await listPending();
  pendingCount.value = actions.length;
}

async function enqueue(action: PendingOfflineAction) {
  const normalized = createAction(action);

  if (hasIndexedDB()) {
    try {
      await withStore("readwrite", (store) => store.put(normalized));
      await refreshPendingCount();
      return normalized;
    } catch {
      // Fall through to localStorage when the browser blocks IndexedDB.
    }
  }

  const actions = readFallback();
  actions.push(normalized);
  writeFallback(actions);
  return normalized;
}

async function listPending(): Promise<Required<PendingOfflineAction>[]> {
  if (hasIndexedDB()) {
    try {
      const records = await withStore<Required<PendingOfflineAction>[]>("readonly", (store) => store.getAll());
      if (records) {
        pendingCount.value = records.length;
        return records;
      }
    } catch {
      // Fall through to localStorage.
    }
  }

  const records = readFallback();
  pendingCount.value = records.length;
  return records;
}

async function removeAction(id: string) {
  if (hasIndexedDB()) {
    try {
      await withStore("readwrite", (store) => store.delete(id));
      await refreshPendingCount();
      return;
    } catch {
      // Fall through to localStorage.
    }
  }

  writeFallback(readFallback().filter((action) => action.id !== id));
}

async function flush(handler: (action: Required<PendingOfflineAction>) => Promise<boolean>): Promise<OfflineFlushResult> {
  if (!online.value) return { synced: 0, failed: 0 };

  const actions = await listPending();
  let synced = 0;
  let failed = 0;

  for (const action of actions) {
    try {
      const ok = await handler(action);
      if (ok) {
        await removeAction(action.id);
        synced += 1;
      } else {
        failed += 1;
      }
    } catch {
      failed += 1;
    }
  }

  return { synced, failed };
}

if (typeof window !== "undefined") {
  window.addEventListener("online", () => {
    online.value = true;
  });
  window.addEventListener("offline", () => {
    online.value = false;
  });
}

export function useOfflineSync() {
  return {
    enqueue,
    flush,
    listPending,
    pendingCount,
    isOnline: computed(() => online.value),
  };
}
