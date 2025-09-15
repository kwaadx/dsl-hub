import { handleRequest } from '@/utils/handleRequest'

class AuthService {
  async login(user) {
    return handleRequest('post', 'auth/login', user)
  }

  async logout() {
    return handleRequest('post', 'auth/logout')
  }

  async refreshToken() {
    return handleRequest('post', 'auth/refresh-token')
  }
}

export default new AuthService()
