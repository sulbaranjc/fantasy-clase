-- 006_clases_limite_equipos.sql
-- Petición de Álvaro (correo "Web fantasy clase", 18/09/2026): que un
-- alumno no pueda estar en más de N equipos a la vez en una misma
-- jornada, para repartir a los alumnos más "valiosos" entre managers.
-- Configurable por clase, igual que el presupuesto de manager; 6 es el
-- valor que Álvaro mencionó como referencia si hubiera que fijar uno.

ALTER TABLE clases
    ADD COLUMN limite_equipos_por_jugador SMALLINT UNSIGNED NOT NULL DEFAULT 6;
