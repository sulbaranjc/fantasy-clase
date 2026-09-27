/**
 * Envío de los formularios de clase (alta y configuración) como JSON,
 * en vez de un submit tradicional del navegador.
 *
 * La validación HTML5 (required, min, etc.) ya la gestiona validaciones.js;
 * aquí solo armamos el payload y mostramos los errores que devuelva el
 * servidor, que es la validación real y definitiva (Pydantic).
 *
 * Los dos formularios viven en páginas distintas (listado / dashboard) y
 * nunca coinciden en el DOM a la vez, así que cada inicializador es
 * independiente: si uno no encuentra su formulario, no debe impedir que
 * el otro registre el suyo.
 */
(function () {
  "use strict";

  function inicializarFormularioNuevaClase() {
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
  }

  function inicializarFormularioConfiguracion() {
    const formulario = document.querySelector("#form-config-clase");
    if (!formulario) return;

    formulario.addEventListener("submit", async function (evento) {
      evento.preventDefault();
      if (!formulario.checkValidity()) {
        formulario.classList.add("was-validated");
        return;
      }

      const datos = Object.fromEntries(new FormData(formulario).entries());
      datos.presupuesto_manager = Number(datos.presupuesto_manager);
      datos.limite_equipos_por_jugador = Number(datos.limite_equipos_por_jugador);

      const alerta = document.querySelector("#alerta-config-clase");
      const exito = document.querySelector("#exito-config-clase");
      alerta.classList.add("d-none");
      exito.classList.add("d-none");

      try {
        const respuesta = await fetch(formulario.dataset.action, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(datos),
        });

        if (!respuesta.ok) {
          const error = await respuesta.json().catch(() => null);
          alerta.textContent = (error && error.detail) || "No se pudieron guardar los cambios.";
          alerta.classList.remove("d-none");
          return;
        }

        exito.classList.remove("d-none");
      } catch (e) {
        alerta.textContent = "Error de conexión con el servidor.";
        alerta.classList.remove("d-none");
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    inicializarFormularioNuevaClase();
    inicializarFormularioConfiguracion();
  });
})();
