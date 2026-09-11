-- 001_init_schema.sql
-- Esquema inicial de "Fantasy de Clase".
-- Convención del proyecto: sin ORM/Alembic; el esquema evoluciona con scripts
-- numerados y versionados a mano (002_..., 003_..., etc.), aplicados en orden.

SET NAMES utf8mb4;
SET time_zone = '+00:00';

-- Clase / temporada gestionada por el profesor. Un profesor puede tener
-- varias clases propias en paralelo (no es un sistema multi-profesor).
CREATE TABLE IF NOT EXISTS clases (
    id                      INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nombre                  VARCHAR(120)    NOT NULL,
    fecha_inicio            DATE            NOT NULL,
    fecha_fin               DATE            NOT NULL,
    duracion_jornada_dias   TINYINT UNSIGNED NOT NULL DEFAULT 14,
    ventana_fichaje_horas   TINYINT UNSIGNED NOT NULL DEFAULT 24,
    valor_inicial_jugador   SMALLINT UNSIGNED NOT NULL DEFAULT 20,
    valor_minimo_jugador    SMALLINT UNSIGNED NOT NULL DEFAULT 10,
    factor_recalculo_valor  DECIMAL(4,3)    NOT NULL DEFAULT 0.100, -- 10% de los puntos de la jornada
    presupuesto_manager     SMALLINT UNSIGNED NOT NULL DEFAULT 120,
    activa                  BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Alumnos de una clase. Cada alumno es simultáneamente "jugador" (recibe
-- eventos y puntos) y "manager" (ficha plantillas).
CREATE TABLE IF NOT EXISTS alumnos (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    clase_id        INT UNSIGNED NOT NULL,
    nombre          VARCHAR(120) NOT NULL,
    username        VARCHAR(60)  NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    valor_actual    SMALLINT UNSIGNED NOT NULL,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_alumnos_clase FOREIGN KEY (clase_id) REFERENCES clases(id) ON DELETE CASCADE,
    UNIQUE KEY uq_alumnos_username_clase (clase_id, username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Cuenta del profesor. Administra varias clases propias.
CREATE TABLE IF NOT EXISTS profesores (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(120) NOT NULL,
    username        VARCHAR(60)  NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Catálogo de eventos y su puntuación, propio de cada clase/temporada.
CREATE TABLE IF NOT EXISTS catalogo_puntos (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    clase_id    INT UNSIGNED NOT NULL,
    nombre      VARCHAR(160) NOT NULL,
    puntos      SMALLINT     NOT NULL, -- puede ser negativo
    activo      BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_catalogo_clase FOREIGN KEY (clase_id) REFERENCES clases(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Jornadas de dos semanas dentro de la temporada, con su ventana de fichajes.
CREATE TABLE IF NOT EXISTS jornadas (
    id                      INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    clase_id                INT UNSIGNED NOT NULL,
    numero                  TINYINT UNSIGNED NOT NULL,
    fecha_inicio            DATE NOT NULL,
    fecha_fin               DATE NOT NULL,
    apertura_fichajes       DATETIME NOT NULL,
    cierre_fichajes         DATETIME NOT NULL,
    cerrada                 BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_jornadas_clase FOREIGN KEY (clase_id) REFERENCES clases(id) ON DELETE CASCADE,
    UNIQUE KEY uq_jornadas_clase_numero (clase_id, numero)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Eventos puntuales registrados por el profesor sobre un alumno.
CREATE TABLE IF NOT EXISTS eventos (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    clase_id            INT UNSIGNED NOT NULL,
    alumno_id           INT UNSIGNED NOT NULL,
    jornada_id          INT UNSIGNED NOT NULL,
    catalogo_punto_id   INT UNSIGNED NOT NULL,
    fecha               DATE NOT NULL,
    nota_numerica       DECIMAL(4,2) NULL, -- p.ej. 8.70 en un examen; opcional
    comentario          VARCHAR(255) NULL,
    puntos_otorgados    SMALLINT NOT NULL, -- copia inmutable de catalogo_puntos.puntos en el momento del registro
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_eventos_clase    FOREIGN KEY (clase_id) REFERENCES clases(id) ON DELETE CASCADE,
    CONSTRAINT fk_eventos_alumno   FOREIGN KEY (alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE,
    CONSTRAINT fk_eventos_jornada  FOREIGN KEY (jornada_id) REFERENCES jornadas(id) ON DELETE CASCADE,
    CONSTRAINT fk_eventos_catalogo FOREIGN KEY (catalogo_punto_id) REFERENCES catalogo_puntos(id),
    INDEX idx_eventos_alumno_jornada (alumno_id, jornada_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Plantilla fichada por un manager (alumno) en una jornada.
CREATE TABLE IF NOT EXISTS plantillas (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    jornada_id      INT UNSIGNED NOT NULL,
    manager_id      INT UNSIGNED NOT NULL,
    capitan_id      INT UNSIGNED NOT NULL, -- debe coincidir con uno de los 5 en plantilla_jugadores
    generada_automaticamente BOOLEAN NOT NULL DEFAULT FALSE, -- repetición por no fichar a tiempo
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_plantillas_jornada FOREIGN KEY (jornada_id) REFERENCES jornadas(id) ON DELETE CASCADE,
    CONSTRAINT fk_plantillas_manager FOREIGN KEY (manager_id) REFERENCES alumnos(id) ON DELETE CASCADE,
    CONSTRAINT fk_plantillas_capitan FOREIGN KEY (capitan_id) REFERENCES alumnos(id),
    UNIQUE KEY uq_plantillas_jornada_manager (jornada_id, manager_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Los 5 jugadores fichados en una plantilla, con el valor vigente al fichar
-- (necesario para poder auditar el respeto del presupuesto en su momento).
CREATE TABLE IF NOT EXISTS plantilla_jugadores (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    plantilla_id    INT UNSIGNED NOT NULL,
    jugador_id      INT UNSIGNED NOT NULL,
    valor_al_fichar SMALLINT UNSIGNED NOT NULL,
    CONSTRAINT fk_plantilla_jugadores_plantilla FOREIGN KEY (plantilla_id) REFERENCES plantillas(id) ON DELETE CASCADE,
    CONSTRAINT fk_plantilla_jugadores_jugador FOREIGN KEY (jugador_id) REFERENCES alumnos(id),
    UNIQUE KEY uq_plantilla_jugador (plantilla_id, jugador_id) -- impide fichar 2 veces al mismo jugador
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Historial del valor de mercado de cada jugador al cierre de cada jornada.
-- Permite recalcular en cascada cuando se corrige un evento retroactivamente.
CREATE TABLE IF NOT EXISTS valor_jugador_historico (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    alumno_id   INT UNSIGNED NOT NULL,
    jornada_id  INT UNSIGNED NOT NULL,
    valor       SMALLINT UNSIGNED NOT NULL,
    CONSTRAINT fk_valor_hist_alumno  FOREIGN KEY (alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE,
    CONSTRAINT fk_valor_hist_jornada FOREIGN KEY (jornada_id) REFERENCES jornadas(id) ON DELETE CASCADE,
    UNIQUE KEY uq_valor_hist_alumno_jornada (alumno_id, jornada_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
