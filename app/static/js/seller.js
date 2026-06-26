window.showPage = function (pageId) {
  document.querySelectorAll(".page-view").forEach((page) => page.classList.add("hidden"));
  document.getElementById(pageId)?.classList.remove("hidden");
};

window.toggleSidebar = function () {};

window.toggleProStatus = async function (checkbox) {
  try {
    const data = await SevarApi.put("/api/v1/sellers/availability", { is_available: checkbox.checked });
    const on = data.is_available;
    document.getElementById("statusText").textContent = on ? "مستعد للطلبات" : "غير متاح";
    document.getElementById("statusDot").className = `w-2.5 h-2.5 ${on ? "bg-green-500 animate-pulse" : "bg-gray-400"} rounded-full`;
  } catch (err) {
    checkbox.checked = !checkbox.checked;
    alert(err.message);
  }
};

window.acceptClientDemand = async function (_name, _budget, _phone, requestId) {
  const id = requestId || document.querySelector("[data-request-id]")?.dataset.requestId;
  if (!id) return alert("No request selected");
  await SevarApi.post(`/api/v1/requests/${id}/accept`, {});
  await loadSellerDashboard();
};

window.rejectClientDemand = async function (requestId) {
  await SevarApi.post(`/api/v1/requests/${requestId}/reject`, {});
  await loadSellerDashboard();
};

window.saveProfileChanges = async function () {
  const name = document.getElementById("txtFormName").value;
  const city = document.getElementById("txtFormCity").value;
  const categoryId = Number(document.getElementById("selFormService").value) || 1;
  await SevarApi.put("/api/v1/users/profile", { full_name: name, city, location: city, user_type: "seller" });
  await SevarApi.put("/api/v1/users/seller-info", {
    service_category_id: categoryId,
    years_experience: 0,
    service_description: "خدمة مهنية",
    primary_language: "AR"
  });
  document.getElementById("lblProfileName").textContent = name;
  document.getElementById("lblProfileCity").textContent = city;
  showPage("dashboardPage");
};

window.changeProfilePicture = async function (event) {
  const file = event.target.files[0];
  if (!file) return;
  const form = new FormData();
  form.append("file", file);
  const data = await SevarApi.upload("/api/v1/uploads/avatar", form);
  document.querySelectorAll("#profileAvatarImg,#navAvatar").forEach((img) => (img.src = data.url));
};
window.updateProfilePhoto = window.changeProfilePicture;

window.loadSellerDashboard = async function () {
  const dashboard = await SevarApi.get("/api/v1/sellers/dashboard");
  document.getElementById("statusToggle").checked = dashboard.is_available;
  await loadSellerMatches(dashboard.recent_matches || []);
};

window.loadSellerMatches = async function (prefetched) {
  const data = prefetched ? { matches: prefetched } : await SevarApi.get("/api/v1/requests/matches");
  const container = document.getElementById("liveDemandsContainer");
  if (!container) return;
  const matches = data.matches || [];
  if (!matches.length) {
    container.innerHTML = `<div class="bg-gray-50 border border-gray-200 p-4 rounded-xl text-sm text-gray-500 text-right">لا توجد طلبات مطابقة حاليا.</div>`;
    return;
  }
  container.innerHTML = matches.map((match) => {
    const req = match.request;
    return `
      <div data-request-id="${req.id}" class="bg-gray-50 border border-gray-200/80 p-4 rounded-xl flex flex-col gap-3 text-right hover:border-neutral-900 transition">
        <div class="flex justify-between items-start">
          <div><span class="px-2 py-0.5 bg-neutral-900 text-white text-[10px] font-black rounded-md ml-2">${req.service_category?.name_ar || ""}</span><strong class="text-sm font-black text-neutral-900">${req.buyer?.full_name || "زبون"}</strong></div>
          <span class="text-xs font-black text-green-600 bg-green-50 px-2.5 py-1 rounded-lg">${req.budget} درهم</span>
        </div>
        <p class="text-xs text-gray-500 leading-relaxed bg-white p-2.5 rounded-lg border border-gray-100">${req.description || ""}</p>
        <div class="flex justify-between items-center text-[11px] text-gray-400 mt-1">
          <span>الموقع: ${req.address}</span>
          <button onclick="acceptClientDemand('', '', '', ${req.id})" class="px-4 py-2 bg-neutral-900 text-white font-bold rounded-lg text-xs transition shadow-sm">قبول</button>
        </div>
      </div>`;
  }).join("");
};

async function loadServicesIntoSelect() {
  const select = document.getElementById("selFormService");
  if (!select) return;
  const data = await SevarApi.get("/api/v1/services");
  select.innerHTML = data.services.map((service) => `<option value="${service.id}">${service.name_ar}</option>`).join("");
}

document.addEventListener("DOMContentLoaded", () => {
  loadServicesIntoSelect().catch(console.warn);
  loadSellerDashboard().catch(console.warn);
});
