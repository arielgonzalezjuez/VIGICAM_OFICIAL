document.addEventListener("DOMContentLoaded", function () {
  const menuToggle = document.getElementById("menuToggle");
  const sidebar = document.getElementById("rightSidebar");
  const overlay = document.getElementById("overlay");

  function toggleSidebar() {
    sidebar.classList.toggle("active");
    overlay.classList.toggle("active");

    // Bloquear/desbloquear scroll del body
    document.body.style.overflow = sidebar.classList.contains("active")
      ? "hidden"
      : "auto";
  }

  // Evento para el botón de menú
  menuToggle.addEventListener("click", function (e) {
    e.stopPropagation();
    toggleSidebar();
  });

  // Cerrar al hacer clic en el overlay
  overlay.addEventListener("click", toggleSidebar);

  // Cerrar al hacer clic fuera en móviles
  if (window.innerWidth <= 768) {
    document.addEventListener("click", function (e) {
      if (!sidebar.contains(e.target) && e.target !== menuToggle) {
        sidebar.classList.remove("active");
        overlay.classList.remove("active");
        document.body.style.overflow = "auto";
      }
    });
  }
});

// Función para abrir el modal de registro
function openAddModal() {
  // Redirigir a la página de trabajadores si no estamos en ella
  if (!window.location.href.includes("trabajadores")) {
    window.location.href = '{% url "trabajadores" %}';
    return;
  }

  // Abrir el modal después de un pequeño retraso para asegurar la carga
  setTimeout(() => {
    const modal = document.getElementById("addPersonModal");
    if (modal) {
      modal.classList.remove("hidden");
      document.body.style.overflow = "hidden";
    }
  }, 100);
}

// Listener para cerrar el modal con Escape
document.addEventListener("keydown", (e) => {
  if (
    e.key === "Escape" &&
    document.getElementById("addPersonModal").classList.contains("hidden") ===
      false
  ) {
    closeModal();
  }
});

// Función para cerrar el modal
function closeModal() {
  document.getElementById("addPersonModal").classList.add("hidden");
  document.body.style.overflow = "";
}

// Cerrar modal con Escape
document.addEventListener("keydown", (e) => {
  if (
    e.key === "Escape" &&
    document.getElementById("addCameraModal").style.display === "flex"
  ) {
    closeCameraModal();
  }
});

// Función para cerrar el modal
function closeCameraModal() {
  document.getElementById("addCameraModal").style.display = "none";
  document.body.style.overflow = "";
}
