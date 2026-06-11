import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getNetworks, deleteNetwork } from '../../api/networks';
import { getHost } from '../../api/hosts';
import CreateNetworkForm from './CreateNetworkForm';

export default function NetworkDashboard() {
    const { hostId } = useParams();
    const navigate = useNavigate();

    const [networks, setNetworks] = useState([]);
    const [host, setHost] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const loadData = async () => {
        try {
            setLoading(true);
            setError('');
            const [netRes, hostRes] = await Promise.all([
                getNetworks(hostId),
                getHost(hostId)
            ]);
            setNetworks(netRes.data || []);
            setHost(hostRes.data);
        } catch (err) {
            setError(
                err.response?.data?.error ||
                'Failed to load networks and host details.'
            );
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (hostId) {
            loadData();
        }
    }, [hostId]);

    const handleDelete = async (networkId) => {
        if (!window.confirm('Are you sure you want to delete this network? All connected containers will be disconnected.')) return;

        try {
            await deleteNetwork(hostId, networkId);
            setNetworks((prev) =>
                prev.filter((n) => n.id !== networkId)
            );
        } catch (err) {
            alert(
                err.response?.data?.error ||
                'Failed to delete network.'
            );
        }
    };

    if (loading) {
        return (
            <div className="dashboard-page">
                <div className="dashboard-inner" style={{ textAlign: 'center', paddingTop: '4rem' }}>
                    <p className="loading-text">Loading networks dashboard…</p>
                </div>
            </div>
        );
    }

    return (
        <div className="dashboard-page">
            <div className="dashboard-inner">
                {/* Header */}
                <div className="dash-header">
                    <div className="dash-logo">
                        <div className="dash-logo-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2">
                                <rect x="2" y="2" width="20" height="20" rx="3" />
                                <path d="M8 12h8M12 8v8" />
                            </svg>
                        </div>
                        <span className="dash-logo-name">DockerIntegrationHost</span>
                    </div>
                    <button className="btn-logout" onClick={() => navigate('/dashboard')}>
                        &larr; Back to Dashboard
                    </button>
                </div>

                {/* Subtitle / Host Header */}
                <div className="network-host-info-bar" style={{ marginBottom: '20px' }}>
                    <div>
                        <h2 style={{ fontSize: '22px', fontWeight: 600, color: '#111' }}>Virtual Networks</h2>
                        {host && (
                            <p className="network-host-subtitle" style={{ fontSize: '13px', color: '#666', marginTop: '4px' }}>
                                Infrastructure Daemon: <strong style={{ color: '#111' }}>{host.alias}</strong> ({host.ip_address}:{host.port})
                            </p>
                        )}
                    </div>
                </div>

                {error && (
                    <div className="form-error" style={{ marginBottom: '16px' }}>
                        {error}
                    </div>
                )}

                {/* Main Content Grid */}
                <div className="network-layout-grid">
                    {/* Left: Provision Form */}
                    <div className="network-form-panel">
                        <CreateNetworkForm hostId={hostId} onCreated={loadData} />
                    </div>

                    {/* Right: Network List */}
                    <div className="network-list-panel">
                        <p className="section-label" style={{ marginBottom: '12px' }}>Active Networks ({networks.length})</p>

                        {networks.length === 0 ? (
                            <div className="empty-state" style={{ padding: '2.5rem 1rem' }}>
                                <p className="empty-title">No virtual networks found</p>
                                <p className="empty-sub">Provision a virtual network using the form to get started.</p>
                            </div>
                        ) : (
                            <div className="network-grid">
                                {networks.map((net) => (
                                    <div key={net.id} className="network-card">
                                        <div className="network-card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                                            <h4 className="network-card-name" style={{ fontSize: '15px', fontWeight: 600, color: '#111', margin: 0 }}>{net.name}</h4>
                                            <span className={`network-driver-badge driver-${net.driver}`} style={{ fontSize: '10px', textTransform: 'uppercase', padding: '2px 6px', borderRadius: '4px', fontWeight: 600 }}>
                                                {net.driver}
                                            </span>
                                        </div>

                                        <div className="network-card-details" style={{ display: 'grid', gap: '4px', fontSize: '12px', color: '#666', marginBottom: '12px' }}>
                                            {net.subnet && (
                                                <div className="detail-item" style={{ display: 'flex', gap: '6px' }}>
                                                    <span style={{ color: '#888' }}>Subnet:</span> <code style={{ fontFamily: 'Space Mono, monospace' }}>{net.subnet}</code>
                                                </div>
                                            )}
                                            {net.gateway && (
                                                <div className="detail-item" style={{ display: 'flex', gap: '6px' }}>
                                                    <span style={{ color: '#888' }}>Gateway:</span> <code style={{ fontFamily: 'Space Mono, monospace' }}>{net.gateway}</code>
                                                </div>
                                            )}
                                            <div className="detail-item" style={{ display: 'flex', gap: '6px' }}>
                                                <span style={{ color: '#888' }}>Scope:</span> <span>{net.internal ? 'Internal (Isolated)' : 'External Bridge'}</span>
                                            </div>
                                        </div>

                                        <div className="network-card-actions" style={{ display: 'flex', gap: '8px' }}>
                                            <button
                                                className="btn-secondary"
                                                style={{ padding: '6px 10px', fontSize: '11px', flex: 1 }}
                                                onClick={() => navigate(`/hosts/${hostId}/networks/${net.id}`)}
                                            >
                                                Inspect
                                            </button>
                                            <button
                                                className="btn-secondary btn-delete-net"
                                                style={{ padding: '6px 10px', fontSize: '11px', flex: 1 }}
                                                onClick={() => handleDelete(net.id)}
                                            >
                                                Delete
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}