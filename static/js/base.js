document.addEventListener("DOMContentLoaded", function () {
  // Elementos del DOM
  const menuToggle = document.querySelector(".menu-toggle");
  const sidebar = document.querySelector(".sidebar");
  const menuItems = document.querySelectorAll(".menu-item");

  // Función para cerrar todos los menús
  function closeAllMenus() {
    sidebar.classList.remove("active");
  }

  // Toggle del menú sidebar
  menuToggle.addEventListener("click", function (e) {
    e.stopPropagation();
    sidebar.classList.toggle("active");
  });

  // Cerrar menú al seleccionar una opción del sidebar
  menuItems.forEach((item) => {
    item.addEventListener("click", function () {
      if (window.innerWidth <= 1024) {
        sidebar.classList.remove("active");
      }
    });
  });

  // Cerrar menús al hacer clic fuera
  document.addEventListener("click", function (e) {
    // Solo cerrar si no se hizo clic en ningún elemento de control
    if (
      !e.target.closest(
        ".menu-toggle, .sidebar, .user-dropdown, .user-dropdown-menu"
      )
    ) {
      closeAllMenus();
    }
  });

  // Ajustar el sidebar al cambiar tamaño de pantalla
  window.addEventListener("resize", function () {
    if (window.innerWidth > 1024) {
      sidebar.classList.remove("active");
    }
  });
});
