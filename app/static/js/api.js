window.SevarApi = {
  async request(path, options = {}) {
    const response = await fetch(path, {
      credentials: "include",
      headers: {
        ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...(options.headers || {})
      },
      ...options
    });
    const payload = await response.json().catch(() => ({ success: false, message: "Invalid server response" }));
    if (!response.ok || payload.success === false) {
      throw new Error(payload.message || "Request failed");
    }
    return payload.data || {};
  },
  get(path) {
    return this.request(path);
  },
  post(path, body) {
    return this.request(path, { method: "POST", body: JSON.stringify(body || {}) });
  },
  put(path, body) {
    return this.request(path, { method: "PUT", body: JSON.stringify(body || {}) });
  },
  upload(path, formData) {
    return this.request(path, { method: "POST", body: formData });
  }
};
