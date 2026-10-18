-- Verificación de integración para CP-02-01 y CP-02-02.
--
-- A diferencia de los tests de Python, este archivo comprueba las reglas en
-- PostgreSQL real. Todo ocurre dentro de una transacción que termina con
-- ROLLBACK, por lo que los datos ficticios nunca quedan guardados.

BEGIN;

DO $$
DECLARE
    test_user_id integer;
    test_session_id integer;
    test_macro_id integer;
    saved_break_minutes integer;
    saved_voice_enabled boolean;
    saved_gesture_enabled boolean;
BEGIN
    INSERT INTO users (name, email, password_hash)
    VALUES ('Prueba CP-02', 'cp02@example.test', 'hash-no-real')
    RETURNING id INTO test_user_id;

    -- Si se omiten estas preferencias, PostgreSQL debe asignar 10, true y true.
    INSERT INTO settings (user_id)
    VALUES (test_user_id)
    RETURNING inactivity_break_minutes, voice_enabled, gesture_enabled
    INTO saved_break_minutes, saved_voice_enabled, saved_gesture_enabled;

    IF saved_break_minutes <> 10
       OR saved_voice_enabled IS NOT TRUE
       OR saved_gesture_enabled IS NOT TRUE THEN
        RAISE EXCEPTION 'Los valores por defecto de settings son incorrectos';
    END IF;

    -- La misma cuenta no puede tener dos filas de configuración.
    BEGIN
        INSERT INTO settings (user_id) VALUES (test_user_id);
        RAISE EXCEPTION 'settings.user_id permitió un duplicado';
    EXCEPTION
        WHEN unique_violation THEN NULL;
    END;

    INSERT INTO usage_sessions (user_id)
    VALUES (test_user_id)
    RETURNING id INTO test_session_id;

    INSERT INTO breaks (usage_session_id, started_at)
    VALUES (test_session_id, now());

    INSERT INTO macros (user_id, name)
    VALUES (test_user_id, 'Macro de prueba')
    RETURNING id INTO test_macro_id;

    INSERT INTO macro_triggers (macro_id, trigger_type, trigger_value)
    VALUES (test_macro_id, 'VOICE', 'abrir navegador');

    INSERT INTO macro_actions (
        macro_id,
        action_type,
        action_value,
        execution_order
    )
    VALUES (test_macro_id, 'OPEN_URL', 'https://example.test', 1);

    -- El CHECK debe rechazar cualquier trigger distinto de VOICE o GESTURE.
    BEGIN
        INSERT INTO macro_triggers (macro_id, trigger_type, trigger_value)
        VALUES (test_macro_id, 'INVALID', 'valor');
        RAISE EXCEPTION 'trigger_type aceptó un valor inválido';
    EXCEPTION
        WHEN check_violation THEN NULL;
    END;

    INSERT INTO applications (user_id, device_name, name, executable_path)
    VALUES (test_user_id, 'PC-PRUEBA', 'Navegador', 'C:\\Navegador.exe');

    -- Una aplicación no puede repetirse para el mismo usuario y dispositivo.
    BEGIN
        INSERT INTO applications (user_id, device_name, name, executable_path)
        VALUES (test_user_id, 'PC-PRUEBA', 'Navegador', 'C:\\OtraRuta.exe');
        RAISE EXCEPTION 'applications permitió un duplicado';
    EXCEPTION
        WHEN unique_violation THEN NULL;
    END;

    -- Al borrar el usuario, las FK con ON DELETE CASCADE limpian sus datos.
    DELETE FROM users WHERE id = test_user_id;

    IF EXISTS (
        SELECT 1 FROM settings WHERE user_id = test_user_id
    ) OR EXISTS (
        SELECT 1 FROM usage_sessions WHERE user_id = test_user_id
    ) OR EXISTS (
        SELECT 1 FROM macros WHERE user_id = test_user_id
    ) OR EXISTS (
        SELECT 1 FROM applications WHERE user_id = test_user_id
    ) THEN
        RAISE EXCEPTION 'El borrado en cascada dejó datos dependientes';
    END IF;

    RAISE NOTICE 'CP-02-01 y CP-02-02 verificadas correctamente';
END
$$;

ROLLBACK;
