import { useCallback, useEffect, useState } from 'react';

const STORAGE_KEY = 'hmi.machine.state.v1';
const DEFAULT_STATE = { running: false, estop: false };

const safeParse = (value) => {
    if (!value) return DEFAULT_STATE;
    try {
        const parsed = JSON.parse(value);
        if (typeof parsed !== 'object' || parsed === null) return DEFAULT_STATE;
        return {
            running: !!parsed.running,
            estop: !!parsed.estop
        };
    } catch {
        return DEFAULT_STATE;
    }
};

const readState = () => {
    if (typeof window === 'undefined') return DEFAULT_STATE;
    return safeParse(window.localStorage.getItem(STORAGE_KEY));
};

const persistState = (state) => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    window.dispatchEvent(new CustomEvent('hmi-machine-state', { detail: state }));
};

export default function useMachineState() {
    const [state, setState] = useState(readState);

    useEffect(() => {
        const handleStorage = (event) => {
            if (event.key !== STORAGE_KEY) return;
            setState(safeParse(event.newValue));
        };

        const handleEvent = (event) => {
            if (!event?.detail) return;
            setState({
                running: !!event.detail.running,
                estop: !!event.detail.estop
            });
        };

        window.addEventListener('storage', handleStorage);
        window.addEventListener('hmi-machine-state', handleEvent);
        return () => {
            window.removeEventListener('storage', handleStorage);
            window.removeEventListener('hmi-machine-state', handleEvent);
        };
    }, []);

    const updateState = useCallback((patch) => {
        setState((prev) => {
            const next = {
                running: prev.running,
                estop: prev.estop,
                ...patch
            };
            if (next.estop) next.running = false;
            persistState(next);
            return next;
        });
    }, []);

    return [state, updateState];
}
