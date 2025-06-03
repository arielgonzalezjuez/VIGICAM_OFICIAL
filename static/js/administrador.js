document.addEventListener("DOMContentLoaded", function () {
  // ——— ELEMENTOS ———
  const userList = document.querySelector(".user-list");
  const adminNameInput = document.getElementById("id_username");
  const adminIdInput = document.getElementById("admin-id");
  const passwordRow = document.querySelector(".password-row");
  const passwordBtn = document.querySelector(".password-btn");
  const adminPasswordInput = document.getElementById("id_password");
  const addBtn = document.querySelector(".add-btn");
  const saveBtn = document.querySelector(".save-btn");
  const deleteBtn = document.querySelector(".delete-btn");
  const searchInput = document.querySelector(".search-input");
  const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

  // ——— HELPERS ———
  function updateAdminDetails(item) {
    const id = item.dataset.id;
    const name = item.querySelector("span").textContent.trim();
    adminIdInput.value = id;
    adminNameInput.value = name;
    passwordRow.style.display = "none";
    adminPasswordInput.value = "";
    passwordBtn.textContent = "Cambiar Contraseña";
  }

  function renderUserList(admins) {
    userList.innerHTML = "";
    admins.forEach(({ id, username }) => {
      const div = document.createElement("div");
      div.className = "user-item";
      div.dataset.id = id;
      div.innerHTML = `
        <svg class="user-icon" ...></svg>
        <span>${username}</span>
      `;
      div.addEventListener("click", () => {
        document
          .querySelectorAll(".user-item.selected")
          .forEach((i) => i.classList.remove("selected"));
        div.classList.add("selected");
        updateAdminDetails(div);
      });
      userList.appendChild(div);
    });
    // auto‑select primero
    const first = userList.querySelector(".user-item");
    if (first) {
      first.classList.add("selected");
      updateAdminDetails(first);
    }
  }

  // ——— AJAX ———
  async function postJSON(url, formData) {
    const resp = await fetch(url, {
      method: "POST",
      headers: { "X-CSRFToken": csrfToken },
      body: formData,
    });
    return resp.json();
  }

  // ——— EVENTOS ———

  // Botón Guardar (crear o editar)
  saveBtn.addEventListener("click", async (e) => {
    e.preventDefault();
    if (!adminNameInput.value.trim())
      return alert("Ingresa un nombre de administrador");
    if (!adminIdInput.value && !adminPasswordInput.value)
      return alert("La contraseña es requerida");
    const fd = new FormData();
    fd.append("username", adminNameInput.value.trim());
    if (adminPasswordInput.value)
      fd.append("password", adminPasswordInput.value);
    const url = adminIdInput.value
      ? `/editarAdmin/${adminIdInput.value}/`
      : `/registrarAdmin/`;
    const data = await postJSON(url, fd);
    if (data.success) window.location.reload();
    else alert(data.message);
  });

  // Botón Eliminar
  deleteBtn.addEventListener("click", async () => {
    const sel = document.querySelector(".user-item.selected");
    if (!sel) return alert("Selecciona un administrador primero");
    if (!confirm(`Eliminar a ${sel.querySelector("span").textContent}?`))
      return;
    const data = await postJSON(
      `/eliminarAdmin/${sel.dataset.id}/`,
      new FormData()
    );
    if (data.success) window.location.reload();
    else alert(data.message);
  });

  // Botón Añadir Nuevo
  addBtn.addEventListener("click", (e) => {
    e.preventDefault();
    document
      .querySelectorAll(".user-item.selected")
      .forEach((i) => i.classList.remove("selected"));
    adminIdInput.value = "";
    adminNameInput.value = "";
    passwordRow.style.display = "flex";
    adminPasswordInput.placeholder = "Contraseña (requerida)";
    adminPasswordInput.value = "";
  });

  // Cambiar Contraseña
  passwordBtn.addEventListener("click", (e) => {
    e.preventDefault();
    if (passwordRow.style.display === "flex") {
      passwordRow.style.display = "none";
      passwordBtn.textContent = "Cambiar Contraseña";
      adminPasswordInput.value = "";
    } else {
      passwordRow.style.display = "flex";
      passwordBtn.textContent = "Cancelar";
      adminPasswordInput.focus();
    }
  });

  // Búsqueda en servidor
  let searchTimeout;
  searchInput.addEventListener("input", () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(async () => {
      const q = searchInput.value.trim();
      const resp = await fetch(`/buscarAdmin/?q=${encodeURIComponent(q)}`);
      const json = await resp.json();
      renderUserList(json.administradores);
    }, 300);
  });

  // Inicialización: cargar lista inicial
  // (ya se hace en el template, pero si quieres refrescar vía AJAX al cargar:)
  renderUserList(
    Array.from(document.querySelectorAll(".user-item")).map((item) => ({
      id: item.dataset.id,
      username: item.querySelector("span").textContent,
    }))
  );
});
