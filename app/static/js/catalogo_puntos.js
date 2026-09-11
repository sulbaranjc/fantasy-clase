/**
 * Alta de tipos de evento y activar/desactivar, enviando JSON a la API
 * (mismo patrón que clases.js: la validación real vive en el servidor).
 */
(function () {
  "use strict";

  function mostrarError(alerta, mensaje) {
    alerta.textContent = mensaje;
    alerta.classList.remove("d-none");
  }

  document.addEventListener("DOMContentLoaded", function () {
    const formulario = document.querySelector("#form-nuevo-evento");
    const alerta = document.querySelector("#alerta-nuevo-evento");

    if (formulario) {
      formulario.addEventListener("submit", async function (evento) {
        evento.preventDefault();
        if (!formulario.checkValidity()) {
          formulario.classList.add("was-validated");
          return;
        }

        const datos = Object.fromEntries(new FormData(formulario).entries());
        datos.puntos = Number(datos.puntos);
        alerta.classList.add("d-none");

        try {
          const respuesta = await fetch(formulario.action, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(datos),
          });

          if (!respuesta.ok) {
            const error = await respuesta.json().catch(() => null);
            mostrarError(alerta, (error && error.detail) || "No se pudo crear el evento.");
            return;
          }

          window.location.reload();
        } catch (e) {
          mostrarError(alerta, "Error de conexión con el servidor.");
        }
      });
    }

    document.querySelectorAll("[data-toggle-activo]").forEach(function (boton) {
      boton.addEventListener("click", async function () {
        const id = boton.dataset.toggleActivo;
        const nombre = boton.dataset.nombre;
        const puntos = Number(boton.dataset.puntos);
        const activo = boton.dataset.activo === "true";

        const respuesta = await fetch(`/catalogo-puntos/${id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ nombre, puntos, activo: !activo }),
        });

        if (respuesta.ok) {
          window.location.reload();
        }
      });
    });
  });
})();
