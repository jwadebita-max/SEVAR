(function () {
  const buyerPath = ["step-1", "step-2", "step-3", "step-4", "step-5A", "step-welcome-buyer"];
  const sellerPath = ["step-1", "step-2", "step-3", "step-4", "step-5B", "step-6B", "step-cin-upload", "step-7B", "step-8B", "step-9B", "step-10B", "step-welcome-seller"];
  let path = buyerPath;
  let index = 0;
  let verifiedPhone = "";

  function activeStepId() {
    return path[index];
  }

  function showStep(id) {
    document.querySelectorAll(".form-step").forEach((step) => step.classList.remove("step-active"));
    const step = document.getElementById(id);
    if (step) step.classList.add("step-active");
    const progress = document.getElementById("main-progress");
    if (progress) progress.style.width = `${((index + 1) / path.length) * 100}%`;
  }

  window.goToNextStep = async function () {
    try {
      const id = activeStepId();
      if (id === "step-1") await requestOtp();
      if (id === "step-2") await verifyOtp();
      if (id === "step-3") await submitBasicProfile();
      if (id === "step-4") {
        const role = document.querySelector("input[name='user-role']:checked")?.value;
        if (!role) throw new Error("Choose buyer or seller");
        path = role === "seller" ? sellerPath : buyerPath;
      }
      if (id === "step-5A") await submitBuyerProfile();
      if (id === "step-welcome-buyer") return (window.location.href = "/buyer");
      if (id === "step-welcome-seller") return (window.location.href = "/seller");
      if (["step-5B", "step-6B", "step-7B", "step-8B", "step-9B", "step-10B"].includes(id)) await submitSellerProfile(false);
      index = Math.min(index + 1, path.length - 1);
      showStep(activeStepId());
    } catch (err) {
      alert(err.message);
    }
  };

  window.goToPreviousStep = function () {
    index = Math.max(index - 1, 0);
    showStep(activeStepId());
  };

  window.requestOtp = async function () {
    const phone = document.getElementById("phone-input").value;
    const data = await SevarAuth.requestOtp(phone);
    verifiedPhone = data.phone_number;
    if (data.development_otp) alert(`OTP: ${data.development_otp}`);
  };

  window.verifyOtp = async function () {
    const otp = [...document.querySelectorAll(".otp-input")].map((input) => input.value).join("");
    await SevarAuth.verifyOtp(verifiedPhone || document.getElementById("phone-input").value, otp);
  };

  window.submitBasicProfile = async function () {
    const fullName = document.getElementById("name-input").value;
    const role = document.querySelector("input[name='user-role']:checked")?.value;
    await SevarApi.put("/api/v1/users/profile", { full_name: fullName, ...(role ? { user_type: role } : {}) });
  };

  window.submitBuyerProfile = async function () {
    const location = document.getElementById("location-input").value;
    await SevarApi.put("/api/v1/users/profile", { user_type: "buyer", location, city: location.split(",")[0].trim() });
  };

  window.submitSellerProfile = async function () {
    await SevarApi.put("/api/v1/users/profile", {
      user_type: "seller",
      full_name: document.getElementById("name-input").value,
      birthdate: document.getElementById("birthdate-input")?.value || undefined,
      gender: document.querySelector("input[name='gender']:checked")?.value || undefined,
      citizenship: document.getElementById("country-select")?.value || undefined,
      city: "Rabat",
      location: "Rabat"
    });
    await SevarApi.put("/api/v1/users/seller-info", {
      service_category_id: 1,
      cin_number: document.getElementById("cin-input")?.value || undefined,
      years_experience: document.getElementById("experience-input")?.value || 0,
      service_description: document.getElementById("description-input")?.value || "خدمة مهنية",
      primary_language: document.getElementById("language-select")?.value || "AR"
    });
  };

  window.triggerCinUpload = function (side) {
    document.getElementById(side === "front" ? "input-cin-front" : "input-cin-back").click();
  };

  window.previewCinImage = async function (input, side) {
    const file = input.files[0];
    if (!file) return;
    const box = document.getElementById(side === "front" ? "cin-front-box" : "cin-back-box");
    box.style.backgroundImage = `url(${URL.createObjectURL(file)})`;
    box.classList.add("has-image");
    const form = new FormData();
    form.append("file", file);
    form.append("side", side);
    try {
      await SevarApi.upload("/api/v1/uploads/cin", form);
    } catch (err) {
      console.warn(err.message);
    }
  };

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".action-next").forEach((button) => button.addEventListener("click", goToNextStep));
    document.getElementById("nav-next-arrow")?.addEventListener("click", goToNextStep);
    document.getElementById("nav-prev-arrow")?.addEventListener("click", goToPreviousStep);
    document.querySelectorAll(".auto-submit-radio").forEach((radio) => radio.addEventListener("change", goToNextStep));
    document.querySelector(".btn-resend")?.addEventListener("click", requestOtp);
    document.querySelectorAll(".btn-exit").forEach((button) => button.addEventListener("click", () => (window.location.href = "/login")));
    document.querySelectorAll(".otp-input").forEach((input, idx, inputs) => {
      input.addEventListener("input", () => {
        if (input.value && inputs[idx + 1]) inputs[idx + 1].focus();
      });
    });
    showStep(activeStepId());
  });
})();
