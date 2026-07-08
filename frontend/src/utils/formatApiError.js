export function formatApiError(error, fallbackMessage) {
  const data = error?.response?.data;

  if (!data) {
    return fallbackMessage;
  }

  if (typeof data.detail === 'string' && data.detail.trim()) {
    return data.detail;
  }

  if (typeof data.error === 'string' && data.error.trim()) {
    return data.error;
  }

  if (typeof data === 'string' && data.trim()) {
    return data;
  }

  if (typeof data === 'object') {
    const messages = Object.entries(data).flatMap(([field, value]) => {
      const items = Array.isArray(value) ? value : [value];
      return items
        .filter((item) => typeof item === 'string' && item.trim())
        .map((item) => `${field}: ${item}`);
    });

    if (messages.length > 0) {
      return messages.join(' ');
    }
  }

  return fallbackMessage;
}
