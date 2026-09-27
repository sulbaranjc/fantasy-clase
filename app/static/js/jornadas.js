/**
 * Botón "Generar calendario": dispara POST /jornadas/generar.
 * Botones "Abrir ahora" / "Cerrar ahora" por jornada: fuerzan la ventana
 * de fichajes al instante actual (petición de Álvaro: poder controlar el
 * mercado manualmente, por ejemplo en clase, sin esperar a la fecha
 * calculada automáticamente). Todos recargan la página al terminar, para
 * mostrar el resultado o el error del servidor.
 */
(function () {
  "use strict";

  function mostrarError(mensaje) {
    const alerta = document.querySelector("#alerta-jornadas");
    alerta.textContent = mensaje;
    alerta.classList.remove("d-none");
  }

  async function accionarBoton(url, mensajeError) {
    const alerta = document.querySelector("#alerta-jornadas");
    alerta.classList.add("d-none");

    const respuesta = await fetch(url, { method: "POST" });

    if (!respuesta.ok) {
      const error = await respuesta.json().catch(() => null);
      mostrarError((error && error.detail) || mensajeError);
      return;
    }

    window.location.reload();
  }

  document.addEventListener("DOMContentLoaded", function () {
    const botonGenerar = document.querySelector("#btn-generar-calendario");
    botonGenerar?.addEventListener("click", function () {
      accionarBoton(botonGenerar.dataset.action, "No se pudo generar el calendario.");
    });

    document.querySelectorAll(".btn-abrir-fichajes").forEach(function (boton) {
      boton.addEventListener("click", function () {
        accionarBoton(`/jornadas/${boton.dataset.jornadaId}/abrir-fichajes`, "No se pudo abrir la ventana de fichajes.");
      });
    });

    document.querySelectorAll(".btn-cerrar-fichajes").forEach(function (boton) {
      boton.addEventListener("click", function () {
        accionarBoton(`/jornadas/${boton.dataset.jornadaId}/cerrar-fichajes`, "No se pudo cerrar la ventana de fichajes.");
      });
    });
  });
})();
