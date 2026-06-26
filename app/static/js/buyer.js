let selectedServiceId = null;

window.showPage = function (pageId) {
  document.querySelectorAll(".page-view").forEach((page) => page.classList.add("hidden"));
  document.getElementById(pageId)?.classList.remove("hidden");
};

window.toggleSidebar = function (id) {
  const sidebar = document.getElementById(id);
  const overlay = document.getElementById("sidebarOverlay");
  sidebar?.classList.toggle("translate-x-full");
  overlay?.classList.toggle("hidden");
};

window.searchServices = function (query) {
  document.querySelectorAll(".service-card").forEach((card) => {
    card.style.display = card.innerText.toLowerCase().includes((query || "").toLowerCase()) ? "" : "none";
  });
};

window.openDemandModal = function (title, slugOrId) {
  selectedServiceId = Number(slugOrId) || selectedServiceId || 1;
  document.getElementById("modalServiceTitle").textContent = title;
  document.getElementById("demandModal").classList.remove("hidden");
};

window.closeDemandModal = function () {
  document.getElementById("demandModal").classList.add("hidden");
};

window.resetWelcomeBox = function () {
  document.getElementById("defaultWelcomeBox")?.classList.remove("hidden");
  document.getElementById("proResultsBox")?.classList.add("hidden");
};

window.executeProMatching = async function () {
  await createServiceRequest();
};

window.createServiceRequest = async function () {
  const budget = document.getElementById("modalPriceInput").value;
  const address = document.getElementById("modalAddressInput").value;
  const city = address.split(",").pop().trim() || address;
  const data = await SevarApi.post("/api/v1/requests", {
    service_category_id: selectedServiceId || 1,
    budget,
    address,
    city,
    description: document.getElementById("modalServiceTitle").textContent
  });
  closeDemandModal();
  document.getElementById("defaultWelcomeBox")?.classList.add("hidden");
  const results = document.getElementById("proResultsBox");
  const list = document.getElementById("proListContainer");
  if (results && list) {
    results.classList.remove("hidden");
    results.classList.add("flex");
    list.innerHTML = `<div class="bg-gray-50 border border-gray-200 rounded-xl p-4 text-sm">تم إنشاء الطلب #${data.request.id}. عدد المطابقات: ${data.matches_created}</div>`;
  }
};

window.changeProfilePicture = async function (event) {
  const file = event.target.files[0];
  if (!file) return;
  const form = new FormData();
  form.append("file", file);
  const data = await SevarApi.upload("/api/v1/uploads/avatar", form);
  document.querySelectorAll("#profileAvatarImg,#navAvatar").forEach((img) => (img.src = data.url));
};

async function loadServiceCategories() {
  const container = document.getElementById("servicesListContainer");
  if (!container) return;
  const data = await SevarApi.get("/api/v1/services");
  container.innerHTML = data.services.map((service) => `
    <div onclick="openDemandModal('${service.name_ar}', ${service.id})" class="service-card bg-white rounded-xl shadow-sm border border-gray-200/70 overflow-hidden hover:shadow-md transition flex flex-col sm:flex-row cursor-pointer group">
      <div class="w-full sm:w-40 h-28 bg-gray-100 shrink-0 overflow-hidden"><img src="${service.image_url}" class="w-full h-full object-cover group-hover:scale-105 transition duration-300"></div>
      <div class="p-4 flex flex-col justify-center text-right w-full">
        <h2 class="text-base font-black text-neutral-900 mb-1">${service.name_ar}</h2>
        <p class="text-gray-500 text-xs leading-relaxed">${service.description_ar || ""}</p>
      </div>
    </div>
  `).join("");
  selectedServiceId = data.services[0]?.id || 1;
}

window.loadBuyerRequests = async function () {
  return SevarApi.get("/api/v1/requests/my");
};

document.addEventListener("DOMContentLoaded", () => {
  loadServiceCategories().catch(console.warn);
});
