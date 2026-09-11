-- 004_plantillas_cascade_alumnos.sql
-- Corrige un olvido de la migración 001: `plantilla_jugadores.jugador_id`
-- y `plantillas.capitan_id` referenciaban a `alumnos` sin ON DELETE
-- CASCADE, a diferencia del resto de referencias a alumnos del esquema
-- (fk_alumnos_clase, fk_eventos_alumno, fk_plantillas_manager,
-- fk_valor_hist_alumno). En la práctica esto impedía borrar una clase
-- completa en cuanto existía alguna plantilla: MySQL rechazaba la
-- cascada de alumnos por esta referencia huérfana (detectado por las
-- pruebas de integración del módulo plantillas).
--
-- DROP y ADD de una constraint con el mismo nombre van en sentencias
-- ALTER TABLE separadas: MySQL no lo permite dentro de un mismo statement.

ALTER TABLE plantilla_jugadores
    DROP FOREIGN KEY fk_plantilla_jugadores_jugador;

ALTER TABLE plantilla_jugadores
    ADD CONSTRAINT fk_plantilla_jugadores_jugador
        FOREIGN KEY (jugador_id) REFERENCES alumnos(id) ON DELETE CASCADE;

ALTER TABLE plantillas
    DROP FOREIGN KEY fk_plantillas_capitan;

ALTER TABLE plantillas
    ADD CONSTRAINT fk_plantillas_capitan
        FOREIGN KEY (capitan_id) REFERENCES alumnos(id) ON DELETE CASCADE;
