document.addEventListener("DOMContentLoaded", () => {
  // Password toggle functionality
  const passwordGroups = document.querySelectorAll(".password-group");

  passwordGroups.forEach((group) => {
    const input = group.querySelector("input");
    const toggleButton = group.querySelector(".toggle-password");
    const eyeIcon = toggleButton.querySelector(".eye-icon");
    const eyeOffIcon = toggleButton.querySelector(".eye-off-icon");

    toggleButton.addEventListener("click", () => {
      const type =
        input.getAttribute("type") === "password" ? "text" : "password";
      input.setAttribute("type", type);
      eyeIcon.classList.toggle("hidden");
      eyeOffIcon.classList.toggle("hidden");
    });
  });
});
