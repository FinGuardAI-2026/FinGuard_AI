import React, { useState, useEffect } from 'react';
import { adminService } from '../../services/admin';
import { Card, Badge, Button, Input, Modal, Spinner } from '../../components/ui';
import {
  UserPlus,
  Edit2,
  Trash2,
  Key,
  Shield,
  Search,
  X,
  Activity,
  Clock,
  Smartphone,
  // Globe,
  // Check,
  AlertTriangle,
  // RotateCcw,
  UserX
} from 'lucide-react';
import { formatDate } from "../../utils/dateFormatter";

export function ManageUsers() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const USERS_PER_PAGE = 5;

  // Selection state
  const [selectedUserIds, setSelectedUserIds] = useState([]);

  // Drawer state
  const [selectedUser, setSelectedUser] = useState(null);

  // Modal states
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isResetOpen, setIsResetOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);

  // Active editing/reset states
  const [targetUser, setTargetUser] = useState(null);

  // Form states
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    role: 'Fraud Analyst',
    password: ''
  });
  const [resetPasswordVal, setResetPasswordVal] = useState('');
  const [error, setError] = useState('');
  const [formLoading, setFormLoading] = useState(false);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const data = await adminService.listUsers();
      setUsers(data);
    } catch (err) {
      console.error('Failed to retrieve user list:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleSearchChange = (e) => {
    setSearchQuery(e.target.value);
    setCurrentPage(1);
  };

  const filteredUsers = users.filter(u =>
    u.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    u.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    u.role.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const indexOfLastUser = currentPage * USERS_PER_PAGE;
  const indexOfFirstUser = indexOfLastUser - USERS_PER_PAGE;

  const paginatedUsers = filteredUsers.slice(
    indexOfFirstUser,
    indexOfLastUser
  );

  // Bulk Operations
  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedUserIds(filteredUsers.map(u => u.id || u._id));
    } else {
      setSelectedUserIds([]);
    }
  };

  const handleSelectUser = (userId) => {
    setSelectedUserIds(prev =>
      prev.includes(userId) ? prev.filter(id => id !== userId) : [...prev, userId]
    );
  };

  const handleBulkStatus = async (isActive) => {
    if (selectedUserIds.length === 0) return;
    try {
      setLoading(true);
      await adminService.bulkStatusUpdate(selectedUserIds, isActive);
      await fetchUsers();
      setSelectedUserIds([]);
    } catch {
      alert('Error updating bulk statuses.');
    } finally {
      setLoading(false);
    }
  };

  const handleBulkDelete = async () => {
    if (selectedUserIds.length === 0) return;
    if (!window.confirm(`Are you sure you want to soft-delete these ${selectedUserIds.length} users?`)) return;
    try {
      setLoading(true);
      await adminService.bulkDelete(selectedUserIds);
      await fetchUsers();
      setSelectedUserIds([]);
    } catch {
      alert('Error soft-deleting users.');
    } finally {
      setLoading(false);
    }
  };

  // Create User
  const openCreateModal = () => {
    setFormData({ full_name: '', email: '', role: 'Fraud Analyst', password: '' });
    setError('');
    setIsCreateOpen(true);
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setError('');

    // Simple front-end validation
    const pw = formData.password;
    if (pw.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }
    if (!/[A-Z]/.test(pw) || !/[a-z]/.test(pw) || !/[0-9]/.test(pw) || !/[!@#$%^&*(),.?":{}|<>]/.test(pw)) {
      setError('Password must contain uppercase, lowercase, digit, and a special character');
      return;
    }

    try {
      setFormLoading(true);
      await adminService.createUser(formData);
      setIsCreateOpen(false);
      await fetchUsers();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create user account');
    } finally {
      setFormLoading(false);
    }
  };

  // Edit User
  const openEditModal = (user) => {
    setTargetUser(user);
    setFormData({
      full_name: user.full_name,
      email: user.email,
      role: user.role,
      is_active: user.is_active
    });
    setError('');
    setIsEditOpen(true);
  };

  const handleEditUser = async (e) => {
    e.preventDefault();
    setError('');
    try {
      setFormLoading(true);
      const userId = targetUser.id || targetUser._id;
      await adminService.editUser(userId, {
        full_name: formData.full_name,
        email: formData.email,
        role: formData.role
      });
      setIsEditOpen(false);
      await fetchUsers();
      if (selectedUser && (selectedUser.id === userId || selectedUser._id === userId)) {
        // Refresh details drawer if open
        const updatedUser = users.find(u => (u.id || u._id) === userId);
        setSelectedUser({ ...updatedUser, ...formData });
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to edit user profile');
    } finally {
      setFormLoading(false);
    }
  };

  // Reset Password
  const openResetModal = (user) => {
    setTargetUser(user);
    setResetPasswordVal('');
    setError('');
    setIsResetOpen(true);
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setError('');
    const pw = resetPasswordVal;
    if (pw.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }
    if (!/[A-Z]/.test(pw) || !/[a-z]/.test(pw) || !/[0-9]/.test(pw) || !/[!@#$%^&*(),.?":{}|<>]/.test(pw)) {
      setError('Password must contain uppercase, lowercase, digit, and a special character');
      return;
    }

    try {
      setFormLoading(true);
      await adminService.resetPassword(targetUser.id || targetUser._id, pw);
      setIsResetOpen(false);
      alert('Password reset successfully.');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to reset password');
    } finally {
      setFormLoading(false);
    }
  };

  // Toggle user active status directly
  const handleToggleActive = async (user) => {
    try {
      setLoading(true);
      const userId = user.id || user._id;
      await adminService.editUser(userId, { is_active: !user.is_active });
      await fetchUsers();
      if (selectedUser && (selectedUser.id === userId || selectedUser._id === userId)) {
        setSelectedUser(prev => ({ ...prev, is_active: !prev.is_active }));
      }
    } catch {
      alert('Failed to change user status.');
    } finally {
      setLoading(false);
    }
  };

  // Delete User (Soft Delete)
  const openDeleteModal = (user) => {
    setTargetUser(user);
    setIsDeleteOpen(true);
  };

  const handleDeleteUser = async () => {
    try {
      setFormLoading(true);
      await adminService.deleteUser(targetUser.id || targetUser._id);
      setIsDeleteOpen(false);
      setSelectedUser(null);
      await fetchUsers();
    } catch {
      alert('Failed to delete user.');
    } finally {
      setFormLoading(false);
    }
  };

  // Revoke user session from drawer
  const handleRevokeSession = async (sessionId) => {
    if (!window.confirm('Are you sure you want to revoke this session? The investigator will be logged out immediately.')) return;
    try {
      const userId = selectedUser.id || selectedUser._id;
      await adminService.revokeUserSession(userId, sessionId);

      // Update local state in drawer
      setSelectedUser(prev => ({
        ...prev,
        sessions: prev.sessions.filter(s => s.session_id !== sessionId)
      }));
      await fetchUsers();
    } catch {
      alert('Failed to revoke session. Please try again.');
    }
  };

  return (
    <div className="relative">
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Main Users Card */}
        <div className="flex-1 min-w-0">
          <Card
            title="User Access Management"
            subtitle="Manage provisioned accounts, suspend credentials, reset passwords, and edit roles."
            action={
              <Button
                variant="primary"
                size="sm"
                onClick={openCreateModal}
                className="w-full sm:w-auto"
              >
                <UserPlus size={14} className="mr-1.5" /> Add Investigator
              </Button>
            }
          >
            {/* Filter/Search Bar */}
            <div className="flex flex-col sm:flex-row items-center gap-3 mb-4">
              <Input
                placeholder="Search by name, email, or role..."
                value={searchQuery}
                onChange={handleSearchChange}
                icon={Search}
                className="w-full sm:max-w-xs"
              />

              {/* Bulk operations toolbar */}
              {selectedUserIds.length > 0 && (
                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 p-1.5 rounded-lg bg-slate-900 border border-slate-800 animate-fade-in w-full sm:w-auto">                  <span className="text-[10px] font-bold text-cyan-400 px-2">{selectedUserIds.length} Selected</span>
                  <Button variant="secondary" className="w-full sm:w-auto" size="sm" onClick={() => handleBulkStatus(true)}>
                    Activate
                  </Button>
                  <Button variant="secondary" className="w-full sm:w-auto" size="sm" onClick={() => handleBulkStatus(false)}>
                    Suspend
                  </Button>
                  <Button variant="danger" className="w-full sm:w-auto" size="sm" onClick={handleBulkDelete}>
                    <Trash2 size={12} className="mr-1 inline" /> Soft Delete
                  </Button>
                </div>
              )}
            </div>

            {loading && users.length === 0 ? (
              <div className="flex justify-center items-center py-20">
                <Spinner size="lg" />
              </div>
            ) : (
              <><div className="overflow-x-auto border border-slate-800 rounded-xl">
                <table className="fg-table">
                  <thead>
                    <tr>
                      <th className="w-8 text-center">
                        <input
                          type="checkbox"
                          onChange={handleSelectAll}
                          checked={selectedUserIds.length === filteredUsers.length && filteredUsers.length > 0}
                          className="rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-cyan-500/50" />
                      </th>
                      <th>Investigator</th>
                      <th>Email Address</th>
                      <th>Role Scope</th>
                      <th>Status</th>
                      <th className="text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredUsers.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="text-center py-10 text-xs text-slate-500">
                          No investigators match the query parameters.
                        </td>
                      </tr>
                    ) : (
                      paginatedUsers.map(u => {
                        const uid = u.id || u._id;
                        const isSelected = selectedUserIds.includes(uid);
                        return (
                          <tr
                            key={uid}
                            onClick={() => setSelectedUser(u)}
                            className={`cursor-pointer hover:bg-slate-800/30 transition-all ${selectedUser && (selectedUser.id === uid || selectedUser._id === uid) ? 'bg-slate-800/40 border-l-2 border-l-cyan-500' : ''}`}
                          >
                            <td className="text-center w-8" onClick={(e) => e.stopPropagation()}>
                              <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={() => handleSelectUser(uid)}
                                className="rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-cyan-500/50" />
                            </td>
                            <td className="font-semibold text-slate-200">
                              <div className="flex items-center gap-2">
                                <div
                                  className="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-bold text-slate-950 uppercase"
                                  style={{ backgroundColor: u.avatar_color || '#06b6d4' }}
                                >
                                  {u.full_name.substring(0, 2)}
                                </div>
                                <span>{u.full_name}</span>
                              </div>
                            </td>
                            <td className="font-mono text-xs text-slate-400">{u.email}</td>
                            <td>
                              <Badge variant={u.role === 'Admin' ? 'danger' : 'info'}>
                                <Shield size={10} className="mr-1 inline" /> {u.role}
                              </Badge>
                            </td>
                            <td>
                              <Badge variant={u.is_active ? 'success' : 'warning'}>
                                {u.is_active ? 'Active' : 'Suspended'}
                              </Badge>
                            </td>
                            <td className="text-right" onClick={(e) => e.stopPropagation()}>
                              <div className="flex items-center justify-end gap-1.5">
                                <button
                                  onClick={() => openEditModal(u)}
                                  className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-all"
                                  title="Edit user details"
                                >
                                  <Edit2 size={13} />
                                </button>
                                <button
                                  onClick={() => openResetModal(u)}
                                  className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-all"
                                  title="Reset password"
                                >
                                  <Key size={13} />
                                </button>
                                <button
                                  onClick={() => handleToggleActive(u)}
                                  className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-all"
                                  title={u.is_active ? 'Suspend investigator' : 'Activate investigator'}
                                >
                                  <UserX size={13} className={u.is_active ? 'text-amber-400' : 'text-emerald-400'} />
                                </button>
                                <button
                                  onClick={() => openDeleteModal(u)}
                                  className="p-1.5 rounded bg-red-950/20 hover:bg-red-950/40 text-red-400 hover:text-red-300 transition-all border border-red-900/30"
                                  title="Soft Delete user"
                                >
                                  <Trash2 size={13} />
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mt-4 px-2">
                  <span className="text-xs text-slate-400">
                    Showing {indexOfFirstUser + 1}–
                    {Math.min(indexOfLastUser, filteredUsers.length)} of {filteredUsers.length} users
                  </span>

                  <div className="flex justify-center sm:justify-end items-center gap-2 flex-wrap">
                    <Button
                      variant="secondary"
                      size="sm"
                      disabled={currentPage === 1}
                      onClick={() => setCurrentPage(prev => prev - 1)}
                    >
                      Previous
                    </Button>

                    <span className="text-xs text-slate-300">
                      Page {currentPage}
                    </span>

                    <Button
                      variant="secondary"
                      size="sm"
                      disabled={indexOfLastUser >= filteredUsers.length}
                      onClick={() => setCurrentPage(prev => prev + 1)}
                    >
                      Next
                    </Button>

                  </div>

                </div></>

            )}
          </Card>
        </div>

        {/* User Details Slide Drawer */}
        {
          selectedUser && (
            <div className="w-full lg:w-96 rounded-xl glass border border-slate-700 shadow-2xl p-5 flex flex-col h-auto max-h-[85vh] overflow-y-auto animate-slide-in">
              <div className="flex justify-between items-start pb-3 border-b border-slate-800">
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-full flex items-center justify-center font-bold text-slate-950 uppercase text-sm"
                    style={{ backgroundColor: selectedUser.avatar_color || '#06b6d4' }}
                  >
                    {selectedUser.full_name.substring(0, 2)}
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-slate-200">{selectedUser.full_name}</h4>
                    <p className="text-[10px] text-slate-400 font-mono mt-0.5">{selectedUser.email}</p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedUser(null)}
                  className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-800"
                >
                  <X size={16} />
                </button>
              </div>

              {/* Quick Metadata */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-4 text-[10px]">
                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800/80">
                  <span className="text-slate-500 uppercase block font-bold">Role</span>
                  <span className="text-slate-200 mt-1 font-semibold block">{selectedUser.role}</span>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800/80">
                  <span className="text-slate-500 uppercase block font-bold">Status</span>
                  <span className={`mt-1 font-bold block ${selectedUser.is_active ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {selectedUser.is_active ? 'ACTIVE' : 'SUSPENDED'}
                  </span>
                </div>
              </div>

              {/* Active Sessions */}
              <div className="mt-5">
                <h5 className="text-[11px] font-bold text-slate-300 uppercase flex items-center gap-1.5 mb-2.5">
                  <Activity size={12} className="text-cyan-400" /> Active Session Clusters ({selectedUser.sessions?.length || 0})
                </h5>

                <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                  {(!selectedUser.sessions || selectedUser.sessions.length === 0) ? (
                    <p className="text-[10px] text-slate-500 text-center py-4 bg-slate-900/50 rounded-lg border border-slate-800/60">
                      No active sessions found.
                    </p>
                  ) : (
                    selectedUser.sessions.map((s, idx) => (
                      <div key={idx} className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-[10px] flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                        <div className="space-y-1">
                          <div className="flex items-center gap-1 font-semibold text-slate-200">
                            <Smartphone size={10} className="text-slate-500" />
                            <span>{s.browser} on {s.os} ({s.device_type})</span>
                          </div>
                          <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-3 text-slate-400 font-mono break-all">
                            <span>{s.ip_address}</span>
                            <span>{s.location}</span>
                          </div>
                        </div>
                        <button
                          onClick={() => handleRevokeSession(s.session_id)}
                          className=" w-full sm:w-auto px-2 py-1 rounded bg-red-950/20 text-red-400 border border-red-900/20 hover:bg-red-950/40 text-[9px] font-semibold"
                        >
                          Revoke
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Login History Timeline */}
              <div className="mt-5">
                <h5 className="text-[11px] font-bold text-slate-300 uppercase flex items-center gap-1.5 mb-2.5">
                  <Clock size={12} className="text-cyan-400" /> Login Telemetry Trail
                </h5>
                <div className="border-l border-slate-800 pl-4 space-y-3.5 max-h-56 overflow-y-auto pr-1">
                  {(!selectedUser.login_history || selectedUser.login_history.length === 0) ? (
                    <p className="text-[10px] text-slate-500 py-2">No login history recorded.</p>
                  ) : (
                    selectedUser.login_history.map((lh, idx) => (
                      <div key={idx} className="relative">
                        <span className={`absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full border border-slate-950 ${lh.status === 'Success' ? 'bg-emerald-400' : 'bg-red-400'
                          }`} />
                        <div className="text-[10px]">
                          <div className="flex items-center justify-between text-slate-300 font-semibold">
                            <span>{lh.status === 'Success' ? 'Login Success' : 'Login Failed'}</span>
                            <span className="font-mono text-slate-500">
                              {formatDate(lh.timestamp)}
                            </span>
                          </div>
                          <p className="text-[9px] text-slate-500 mt-0.5">{lh.device} • {lh.ip_address}</p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )
        }
      </div >

      {/* Modals Section */}

      {/* Create User Modal */}
      <Modal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} title="Provision New Investigator Profile" maxWidth="max-w-md">
        <form onSubmit={handleCreateUser} className="space-y-4">
          <Input
            label="Full Name"
            placeholder="e.g. John Doe"
            required
            value={formData.full_name}
            onChange={(e) => setFormData(prev => ({ ...prev, full_name: e.target.value }))}
          />
          <Input
            label="Email Address"
            type="email"
            placeholder="e.g. jdoe@finguard.ai"
            required
            value={formData.email}
            onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
          />
          <div className="w-full">
            <label className="fg-label">Governance Role Assignment</label>
            <select
              className="fg-input"
              value={formData.role}
              onChange={(e) => setFormData(prev => ({ ...prev, role: e.target.value }))}
            >
              <option value="Fraud Analyst">Fraud Analyst</option>
              <option value="Admin">System Administrator</option>
            </select>
          </div>
          <Input
            label="Initial Password"
            type="password"
            placeholder="••••••••"
            required
            helperText="Requires 8+ chars, uppercase, lowercase, digit, and special char."
            value={formData.password}
            onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
          />
          {error && <p className="text-xs text-red-400">{error}</p>}

          <div className="flex flex-col-reverse sm:flex-row justify-end gap-2 pt-3 border-t border-slate-800">
            <Button variant="secondary" className="w-full sm:w-auto"
              onClick={() => setIsCreateOpen(false)} type="button">
              Cancel
            </Button>
            <Button variant="primary" className="w-full sm:w-auto"
              type="submit" isLoading={formLoading}>
              Provision Account
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit User Modal */}
      <Modal isOpen={isEditOpen} onClose={() => setIsEditOpen(false)} title="Edit User Credentials" maxWidth="max-w-md">
        <form onSubmit={handleEditUser} className="space-y-4">
          <Input
            label="Full Name"
            placeholder="e.g. John Doe"
            required
            value={formData.full_name}
            onChange={(e) => setFormData(prev => ({ ...prev, full_name: e.target.value }))}
          />
          <Input
            label="Email Address"
            type="email"
            placeholder="e.g. jdoe@finguard.ai"
            required
            value={formData.email}
            onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
          />
          <div className="w-full">
            <label className="fg-label">Governance Role Assignment</label>
            <select
              className="fg-input"
              value={formData.role}
              onChange={(e) => setFormData(prev => ({ ...prev, role: e.target.value }))}
            >
              <option value="Fraud Analyst">Fraud Analyst</option>
              <option value="Admin">System Administrator</option>
            </select>
          </div>
          {error && <p className="text-xs text-red-400">{error}</p>}

          <div className="flex flex-col-reverse sm:flex-row justify-end gap-2 pt-3 border-t border-slate-800">
            <Button variant="secondary" onClick={() => setIsEditOpen(false)} type="button" className="w-full sm:w-auto">
              Cancel
            </Button>
            <Button variant="primary" type="submit" isLoading={formLoading} className="w-full sm:w-auto">
              Save Credentials
            </Button>
          </div>
        </form>
      </Modal>

      {/* Reset Password Modal */}
      <Modal isOpen={isResetOpen} onClose={() => setIsResetOpen(false)} title="Reset User Password" maxWidth="max-w-md">
        <form onSubmit={handleResetPassword} className="space-y-4">
          <p className="text-xs text-slate-400 leading-relaxed">
            This will directly overwrite the password for <span className="font-semibold text-slate-200">{targetUser?.full_name}</span>.
          </p>
          <Input
            label="New Password"
            type="password"
            placeholder="••••••••"
            required
            helperText="Requires 8+ chars, uppercase, lowercase, digit, and special char."
            value={resetPasswordVal}
            onChange={(e) => setResetPasswordVal(e.target.value)}
          />
          {error && <p className="text-xs text-red-400">{error}</p>}

          <div className="flex flex-col-reverse sm:flex-row justify-end gap-2 pt-3 border-t border-slate-800">
            <Button variant="secondary" className="w-full sm:w-auto" onClick={() => setIsResetOpen(false)} type="button">
              Cancel
            </Button>
            <Button variant="primary" className="w-full sm:w-auto" type="submit" isLoading={formLoading}>
              Overwrite Password
            </Button>
          </div>
        </form>
      </Modal>

      {/* Soft Delete Modal */}
      <Modal isOpen={isDeleteOpen} onClose={() => setIsDeleteOpen(false)} title="Soft Delete Investigator Account" maxWidth="max-w-md">
        <div className="space-y-4">
          <div className="flex gap-3 p-3 rounded-lg bg-red-500/10 text-red-400 border border-red-500/20 text-xs">
            <AlertTriangle size={16} className="shrink-0 mt-0.5" />
            <div>
              <p className="font-bold">Security Notice</p>
              <p className="mt-0.5 leading-relaxed">
                You are about to soft-delete the account for <span className="font-semibold text-white">{targetUser?.full_name} ({targetUser?.email})</span>.
              </p>
            </div>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Soft-deleted accounts are suspended immediately and hidden from general workflows. However, all past audit logs, case investigations, and telemetry associated with this user remain preserved for regulatory compliance.
          </p>

          <div className="flex flex-col-reverse sm:flex-row justify-end gap-2 pt-3 border-t border-slate-800">
            <Button variant="secondary" className="w-full sm:w-auto" onClick={() => setIsDeleteOpen(false)}>
              Cancel
            </Button>
            <Button variant="danger" className="w-full sm:w-auto" onClick={handleDeleteUser} isLoading={formLoading}>
              Soft Delete Account
            </Button>
          </div>
        </div>
      </Modal>
    </div >
  );
}
