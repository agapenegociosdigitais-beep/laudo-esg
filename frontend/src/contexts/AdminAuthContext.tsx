'use client';

import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { adminService } from '@/services/adminService';

interface AdminAuthContextType {
  admin: any | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AdminAuthContext = createContext<AdminAuthContextType | null>(null);

export function AdminAuthProvider({ children }: { children: ReactNode }) {
  const [admin, setAdmin] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('admin_token');
      if (token) {
        try {
          const me = await adminService.getMe();
          setAdmin(me);
        } catch (error) {
          localStorage.removeItem('admin_token');
        }
      }
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const response = await adminService.login(email, password);
      setAdmin(response.admin);
      localStorage.setItem('admin_token', response.access_token);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    localStorage.removeItem('admin_token');
    setAdmin(null);
  }, []);

  return (
    <AdminAuthContext.Provider value={{
      admin,
      isLoading,
      isAuthenticated: !!admin,
      login,
      logout,
    }}>
      {children}
    </AdminAuthContext.Provider>
  );
}

export function useAdminAuth() {
  const context = useContext(AdminAuthContext);
  if (!context) {
    throw new Error('useAdminAuth deve ser usado dentro de AdminAuthProvider');
  }
  return context;
}
