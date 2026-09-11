/**
 * Envío del formulario de alta de clase como JSON al endpoint de la API
 * (POST /clases), en vez de un submit tradicional del navegador.
 *
 * La validación HTML5 (required, min, etc.) ya la gestiona validaciones.js;
 * aquí solo armamos el payload y mostramos los errores que devuelva el
 * servidor, que es la validación real y definitiva (Pydantic).
 */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    const formulario = document.querySelector("#form-nueva-clase");
    if (!formulario) return;

    formulario.addEventListener("submit", async function (evento) {
      evento.preventDefault();
      if (!formulario.checkValidity()) {
        formulario.classList.add("was-validated");
        return;
      }

      const datos = Object.fromEntries(new FormData(formulario).entries());
      datos.presupuesto_manager = Number(datos.presupuesto_manager);

      const alerta = document.querySelector("#alerta-nueva-clase");
      alerta.classList.add("d-none");

      try {
        const respuesta = await fetch(formulario.action, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(datos),
        });

        if (!respuesta.ok) {
          const error = await respuesta.json().catch(() => null);
          const mensaje = error && error.detail
            ? JSON.stringify(error.detail)
            : "No se pudo crear la clase. Revisa los datos.";
          alerta.textContent = mensaje;
          alerta.classList.remove("d-none");
          return;
        }

        window.location.reload();
      } catch (e) {
        alerta.textContent = "Error de conexión con el servidor.";
        alerta.classList.remove("d-none");
      }
    });
  });
})();
