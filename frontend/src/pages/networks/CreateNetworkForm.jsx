import { useState } from 'react';
import { createNetwork } from '../../api/networks';

export default function CreateNetworkForm({ hostId, onCreated }) {
    const initialState = {
        name: '',
        driver: 'bridge',
        subnet: '',
        gateway: '',
        internal: false,
        attachable: true
    };

    const [form, setForm] = useState(initialState);
    const [error, setError] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setForm({
            ...form,
            [name]: type === 'checkbox' ? checked : value
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setIsSubmitting(true);

        const payload = {
            ...form,
            subnet: form.subnet.trim() || null,
            gateway: form.gateway.trim() || null,
        };

        try {
            await createNetwork(hostId, payload);
            onCreated();
            setForm(initialState);
        } catch (err) {
            const apiError = err.response?.data?.error || 'Failed to provision network on engine.';
            setError(apiError);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="creation-form-container" style={{ background: '#fff', border: '1px solid #e5e5e5', borderRadius: '14px', padding: '20px' }}>
            <h4 style={{ fontSize: '14px', fontWeight: 600, color: '#111', marginBottom: '12px', borderBottom: '1px solid #eee', paddingBottom: '8px' }}>
                Provision New Network
            </h4>

            {error && <div className="form-error" style={{ marginBottom: '12px' }}>{error}</div>}

            <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '12px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                    <div className="form-group" style={{ margin: 0 }}>
                        <label className="form-label" style={{ fontSize: '11px', color: '#888', fontWeight: 500, textTransform: 'uppercase', marginBottom: '4px' }}>Network Name*</label>
                        <input
                            type="text"
                            name="name"
                            className="form-input"
                            placeholder="e.g., prod-db-net"
                            value={form.name}
                            onChange={handleChange}
                            required
                        />
                    </div>

                    <div className="form-group" style={{ margin: 0 }}>
                        <label className="form-label" style={{ fontSize: '11px', color: '#888', fontWeight: 500, textTransform: 'uppercase', marginBottom: '4px' }}>Driver Type</label>
                        <select name="driver" className="form-input" value={form.driver} onChange={handleChange}>
                            <option value="bridge">Bridge (Default)</option>
                            <option value="overlay">Overlay (Swarm)</option>
                            <option value="host">Host</option>
                            <option value="none">None</option>
                        </select>
                    </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                    <div className="form-group" style={{ margin: 0 }}>
                        <label className="form-label" style={{ fontSize: '11px', color: '#888', fontWeight: 500, textTransform: 'uppercase', marginBottom: '4px' }}>Subnet (Optional)</label>
                        <input
                            type="text"
                            name="subnet"
                            className="form-input"
                            placeholder="172.18.0.0/16"
                            value={form.subnet}
                            onChange={handleChange}
                        />
                    </div>
                    <div className="form-group" style={{ margin: 0 }}>
                        <label className="form-label" style={{ fontSize: '11px', color: '#888', fontWeight: 500, textTransform: 'uppercase', marginBottom: '4px' }}>Gateway (Optional)</label>
                        <input
                            type="text"
                            name="gateway"
                            className="form-input"
                            placeholder="172.18.0.1"
                            value={form.gateway}
                            onChange={handleChange}
                        />
                    </div>
                </div>

                <div style={{ display: 'flex', gap: '16px', margin: '4px 0' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#555', cursor: 'pointer' }}>
                        <input
                            type="checkbox"
                            name="internal"
                            checked={form.internal}
                            onChange={handleChange}
                        />
                        Internal (Isolated)
                    </label>

                    <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#555', cursor: 'pointer' }}>
                        <input
                            type="checkbox"
                            name="attachable"
                            checked={form.attachable}
                            onChange={handleChange}
                        />
                        Manual Attach
                    </label>
                </div>

                <button
                    type="submit"
                    className="btn-primary"
                    style={{ marginTop: '8px' }}
                    disabled={isSubmitting}
                >
                    {isSubmitting ? 'Provisioning...' : 'Create Virtual Network'}
                </button>
            </form>
        </div>
    );
}