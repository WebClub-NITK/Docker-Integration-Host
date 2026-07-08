import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    inspectNetwork,
    connectContainer,
    disconnectContainer,
} from '../../api/networks';
import { getHost } from '../../api/hosts';

export default function NetworkDetail() {
    const { hostId, networkId } = useParams();
    const navigate = useNavigate();

    const [network, setNetwork] = useState(null);
    const [host, setHost] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const [inputContainerId, setInputContainerId] = useState('');
    const [actionLoading, setActionLoading] = useState(false);

    const loadNetwork = async () => {
        setLoading(true);
        setError('');

        try {
            const [netRes, hostRes] = await Promise.all([
                inspectNetwork(hostId, networkId),
                getHost(hostId)
            ]);
            setNetwork(netRes.data);
            setHost(hostRes.data);
        } catch (err) {
            setError(
                err.response?.data?.error ||
                'Failed to load network details.'
            );
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (hostId && networkId) {
            loadNetwork();
        }
    }, [hostId, networkId]);

    const handleConnectAction = async (e) => {
        e.preventDefault();

        const cleanId = inputContainerId.trim();
        if (!cleanId) return;

        setError('');
        setActionLoading(true);

        try {
            await connectContainer(hostId, networkId, {
                container_id: cleanId,
            });
            setInputContainerId('');
            await loadNetwork();
        } catch (err) {
            setError(
                err.response?.data?.error ||
                'Failed to connect container.'
            );
        } finally {
            setActionLoading(false);
        }
    };

    const handleDisconnectAction = async (containerId) => {
        if (!window.confirm(`Are you sure you want to disconnect container ${containerId.slice(0, 12)} from this network?`)) {
            return;
        }

        try {
            await disconnectContainer(hostId, networkId, {
                container_id: containerId,
                force: false,
            });
            await loadNetwork();
        } catch (err) {
            setError(
                err.response?.data?.error ||
                'Failed to disconnect container.'
            );
        }
    };

    if (loading) {
        return (
            <div className="dashboard-page">
                <div className="dashboard-inner" style={{ textAlign: 'center', paddingTop: '4rem' }}>
                    <p className="loading-text">Loading network details…</p>
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
                    <button className="btn-logout" onClick={() => navigate(`/hosts/${hostId}/networks`)}>
                        &larr; Back to Networks
                    </button>
                </div>

                {error && !network && (
                    <div className="form-error" style={{ marginBottom: '16px' }}>
                        {error}
                    </div>
                )}

                {!network ? (
                    <div className="empty-state">
                        <p className="empty-title">Network not found</p>
                        <p className="empty-sub">The requested virtual network could not be loaded.</p>
                        <button className="btn-primary" style={{ marginTop: '12px', width: 'auto' }} onClick={() => navigate(`/hosts/${hostId}/networks`)}>
                            Back to Networks List
                        </button>
                    </div>
                ) : (
                    <div className="network-detail-container">
                        {/* Info Header */}
                        <div className="network-detail-main-card" style={{ background: '#fff', border: '1px solid #e5e5e5', borderRadius: '14px', padding: '20px', marginBottom: '20px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                                <h2 style={{ fontSize: '20px', fontWeight: 600, color: '#111', margin: 0 }}>
                                    Network: {network.name}
                                </h2>
                                <span className={`network-driver-badge driver-${network.driver}`} style={{ fontSize: '10px', textTransform: 'uppercase', padding: '2px 6px', borderRadius: '4px', fontWeight: 600 }}>
                                    {network.driver}
                                </span>
                            </div>

                            {host && (
                                <p style={{ fontSize: '13px', color: '#666', marginBottom: '16px' }}>
                                    Target Infrastructure: <strong style={{ color: '#111' }}>{host.alias}</strong> ({host.ip_address}:{host.port})
                                </p>
                            )}

                            <div className="network-detail-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '10px' }}>
                                <div className="info-tile" style={{ background: '#f9f9fb', border: '1px solid #eee', borderRadius: '8px', padding: '10px', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                                    <span style={{ fontSize: '9px', textTransform: 'uppercase', color: '#888', fontWeight: 600 }}>SUBNET</span>
                                    <strong style={{ fontSize: '13px', color: '#111', fontFamily: 'Space Mono, monospace' }}>{network.subnet || 'Auto-allocated / None'}</strong>
                                </div>
                                <div className="info-tile" style={{ background: '#f9f9fb', border: '1px solid #eee', borderRadius: '8px', padding: '10px', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                                    <span style={{ fontSize: '9px', textTransform: 'uppercase', color: '#888', fontWeight: 600 }}>GATEWAY</span>
                                    <strong style={{ fontSize: '13px', color: '#111', fontFamily: 'Space Mono, monospace' }}>{network.gateway || 'Auto-allocated / None'}</strong>
                                </div>
                                <div className="info-tile" style={{ background: '#f9f9fb', border: '1px solid #eee', borderRadius: '8px', padding: '10px', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                                    <span style={{ fontSize: '9px', textTransform: 'uppercase', color: '#888', fontWeight: 600 }}>SCOPE</span>
                                    <strong style={{ fontSize: '13px', color: '#111' }}>{network.internal ? 'Isolated (Internal)' : 'Standard (Bridge)'}</strong>
                                </div>
                                <div className="info-tile" style={{ background: '#f9f9fb', border: '1px solid #eee', borderRadius: '8px', padding: '10px', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                                    <span style={{ fontSize: '9px', textTransform: 'uppercase', color: '#888', fontWeight: 600 }}>ATTACHABLE</span>
                                    <strong style={{ fontSize: '13px', color: '#111' }}>{network.attachable ? 'Enabled' : 'Disabled'}</strong>
                                </div>
                            </div>
                        </div>

                        {error && (
                            <div className="form-error" style={{ marginTop: '16px', marginBottom: '16px' }}>
                                {error}
                            </div>
                        )}

                        {/* Split: Connected Containers & Connect Action */}
                        <div className="network-layout-grid">
                            {/* Connected Containers */}
                            <div className="network-list-panel">
                                <p className="section-label" style={{ marginBottom: '12px' }}>
                                    Connected Containers ({Object.keys(network.containers || {}).length})
                                </p>

                                {Object.keys(network.containers || {}).length === 0 ? (
                                    <div className="empty-state" style={{ padding: '2rem 1rem' }}>
                                        <p className="empty-title">No containers connected</p>
                                        <p className="empty-sub">No Docker workloads are currently attached to this network interface.</p>
                                    </div>
                                ) : (
                                    <div style={{ display: 'grid', gap: '10px' }}>
                                        {Object.entries(network.containers || {}).map(([id, info]) => (
                                            <div key={id} className="container-attachment-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#fff', border: '1px solid #e5e5e5', borderRadius: '10px', padding: '10px 14px' }}>
                                                <div>
                                                    <div style={{ fontSize: '14px', fontWeight: 500, color: '#111' }}>
                                                        {info.Name || info.name || 'Unnamed workload'}
                                                    </div>
                                                    <code style={{ fontSize: '11px', color: '#888', fontFamily: 'Space Mono, monospace' }}>
                                                        ID: {id.slice(0, 12)}
                                                    </code>
                                                    {info.IPv4Address && (
                                                        <div style={{ fontSize: '11px', color: '#666', marginTop: '3px' }}>
                                                            IP Address: <code style={{ fontFamily: 'Space Mono, monospace' }}>{info.IPv4Address}</code>
                                                        </div>
                                                    )}
                                                </div>

                                                <button
                                                    className="btn-secondary btn-delete-net"
                                                    style={{ padding: '6px 10px', fontSize: '11px', border: '1px solid #fecaca', background: '#fef2f2', color: '#dc2626' }}
                                                    onClick={() => handleDisconnectAction(id)}
                                                >
                                                    Disconnect
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* Connect Container Form */}
                            <div className="network-form-panel">
                                <div className="creation-form-container" style={{ background: '#fff', border: '1px solid #e5e5e5', borderRadius: '14px', padding: '20px' }}>
                                    <h4 style={{ fontSize: '14px', fontWeight: 600, color: '#111', marginBottom: '12px', borderBottom: '1px solid #eee', paddingBottom: '8px' }}>
                                        Connect Container Workload
                                    </h4>
                                    <form onSubmit={handleConnectAction} style={{ display: 'grid', gap: '12px' }}>
                                        <div className="form-group" style={{ margin: 0 }}>
                                            <label className="form-label" style={{ fontSize: '11px', color: '#888', fontWeight: 500 }}>Container ID or Name*</label>
                                            <input
                                                type="text"
                                                className="form-input"
                                                value={inputContainerId}
                                                onChange={(e) => setInputContainerId(e.target.value)}
                                                placeholder="e.g. 5a1b3c9f2d1e or test-app"
                                                required
                                            />
                                        </div>

                                        <button
                                            type="submit"
                                            className="btn-primary"
                                            style={{ marginTop: 0 }}
                                            disabled={actionLoading}
                                        >
                                            {actionLoading ? 'Connecting...' : 'Attach to Network'}
                                        </button>
                                    </form>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}