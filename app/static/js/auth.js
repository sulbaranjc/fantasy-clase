/**
 * Envío de los formularios de login (alumno y profesor) como JSON al
 * endpoint correspondiente. El servidor responde fijando la cookie de
 * sesión (httpOnly); aquí solo hace falta redirigir tras un login exitoso.
 */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    const alerta = document.querySelector("#alerta-login");

    document.querySelectorAll(".formulario-login").forEach(function (formulario) {
      formulario.addEventListener("submit", async function (evento) {
        evento.preventDefault();
        if (!formulario.checkValidity()) {
          formulario.classList.add("was-validated");
          return;
        }

        const datos = Object.fromEntries(new FormData(formulario).entries());
        alerta.classList.add("d-none");

        try {
          const respuesta = await fetch(formulario.dataset.action, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(datos),
          });

          if (!respuesta.ok) {
            const error = await respuesta.json().catch(() => null);
            alerta.textContent = (error && error.detail) || "No se pudo iniciar sesión.";
            alerta.classList.remove("d-none");
            return;
          }

          window.location.href = "/";
        } catch (e) {
          alerta.textContent = "Error de conexión con el servidor.";
          alerta.classList.remove("d-none");
        }
      });
    });
  });
})();
