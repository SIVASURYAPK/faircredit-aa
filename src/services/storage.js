export function readStorage(key, fallback) {
  try {
    const value = window.localStorage.getItem(key);
    return value ? JSON.parse(value) : fallback;
  } catch {
    return fallback;
  }
}

export function writeStorage(key, value) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
}

export function makeTicket(subject, message) {
  const shortId = Math.random().toString(36).slice(2, 6).toUpperCase();
  return {
    id: `FC-SUP-${shortId}`,
    subject: subject.trim() || message.trim().slice(0, 42) || 'General enquiry',
    status: 'Received',
    updated: 'Just now',
    message: message.trim(),
  };
}
