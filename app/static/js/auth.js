window.SevarAuth = {
  async requestOtp(phoneNumber) {
    return SevarApi.post("/api/v1/auth/phone/request-otp", { phone_number: phoneNumber });
  },
  async verifyOtp(phoneNumber, otp) {
    return SevarApi.post("/api/v1/auth/phone/verify-otp", { phone_number: phoneNumber, otp });
  },
  async me() {
    return SevarApi.get("/api/v1/auth/me");
  },
  async logout() {
    return SevarApi.post("/api/v1/auth/logout", {});
  }
};
