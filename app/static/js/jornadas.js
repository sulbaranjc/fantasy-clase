/**
 * Botón "Generar calendario": dispara POST /jornadas/generar y recarga
 * la página para mostrar el resultado (o el error del servidor).
 */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    const boton = document.querySelector("#btn-generar-calendario");
    if (!boton) return;

    boton.addEventListener("click", async function () {
      const alerta = document.querySelector("#alerta-jornadas");
      alerta.classList.add("d-none");

      const respuesta = await fetch(boton.dataset.action, { method: "POST" });

      if (!respuesta.ok) {
        const error = await respuesta.json().catch(() => null);
        alerta.textContent = (error && error.detail) || "No se pudo generar el calendario.";
        alerta.classList.remove("d-none");
        return;
      }

      window.location.reload();
    });
  });
})();
