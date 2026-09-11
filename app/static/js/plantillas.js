/**
 * Ficha de plantilla: 5 jugadores + capitán, con el presupuesto restante
 * recalculado en vivo (vanilla JS) al marcar/desmarcar jugadores.
 *
 * La validación real y definitiva (presupuesto, duplicados, pertenencia a
 * la clase, ventana de fichajes) la hace el servidor; esto es solo
 * realimentación inmediata para quien está fichando.
 */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    const formulario = document.querySelector("#form-fichar-plantilla");
    if (!formulario) return;

    const checkboxes = Array.from(document.querySelectorAll(".jugador-checkbox"));
    const radiosCapitan = Array.from(document.querySelectorAll(".capitan-radio"));
    const presupuestoUsado = document.querySelector("#presupuesto-usado");
    const presupuestoTotal = document.querySelector("#presupuesto-total");
    const alerta = document.querySelector("#alerta-plantilla");
    const total = window.PRESUPUESTO_TOTAL || 0;

    presupuestoTotal.textContent = total;

    function jugadoresMarcados() {
      return checkboxes.filter((c) => c.checked);
    }

    function actualizarVista() {
      const marcados = jugadoresMarcados();
      const usado = marcados.reduce((suma, c) => suma + Number(c.dataset.valor), 0);
      presupuestoUsado.textContent = usado;
      presupuestoUsado.classList.toggle("text-danger", usado > total);

      const idsMarcados = new Set(marcados.map((c) => c.value));
      radiosCapitan.forEach((radio) => {
        radio.disabled = !idsMarcados.has(radio.value);
        if (radio.disabled) radio.checked = false;
      });
    }

    checkboxes.forEach((c) => c.addEventListener("change", actualizarVista));
    actualizarVista();

    formulario.addEventListener("submit", async function (evento) {
      evento.preventDefault();
      alerta.classList.add("d-none");

      const marcados = jugadoresMarcados();
      const capitanMarcado = radiosCapitan.find((r) => r.checked);
      const managerId = Number(formulario.dataset.managerId);

      if (marcados.length !== 5) {
        alerta.textContent = "Debes fichar exactamente 5 jugadores.";
        alerta.classList.remove("d-none");
        return;
      }
      if (!capitanMarcado) {
        alerta.textContent = "Elige quién es tu capitán entre los 5 fichados.";
        alerta.classList.remove("d-none");
        return;
      }
      const idsMarcados = marcados.map((c) => Number(c.value));
      if (!idsMarcados.includes(managerId)) {
        alerta.textContent = "Debes incluirte a ti mismo entre los 5 jugadores.";
        alerta.classList.remove("d-none");
        return;
      }

      const payload = {
        jornada_id: Number(formulario.dataset.jornadaId),
        manager_id: managerId,
        jugadores_ids: idsMarcados,
        capitan_id: Number(capitanMarcado.value),
      };

      try {
        const respuesta = await fetch(formulario.dataset.action, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (!respuesta.ok) {
          const error = await respuesta.json().catch(() => null);
          alerta.textContent = (error && error.detail) || "No se pudo guardar la plantilla.";
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
