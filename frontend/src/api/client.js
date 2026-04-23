import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || '/api'

const client = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response interceptor for error handling
client.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

/**
 * Fetch all constituencies grouped by district.
 * @param {Object} params - Optional search/filter params
 * @returns {Promise<{total: number, districts: Object}>}
 */
export const getConstituencies = async (params = {}) => {
  const { data } = await client.get('/constituencies/', { params })
  return data
}

/**
 * Run moral match scoring for a constituency.
 * @param {number} constituencyId
 * @param {string} moralInput - Free-text voter values description
 * @returns {Promise<{top3: Array}>}
 */
export const runMoralMatch = async (constituencyId, moralInput) => {
  const { data } = await client.post('/moral-match/', {
    constituency_id: constituencyId,
    moral_input: moralInput,
  })
  return data
}

/**
 * Get win probability predictions for a constituency.
 * @param {number} constituencyId
 * @returns {Promise<{predictions: Array}>}
 */
export const getRealityPrediction = async (constituencyId) => {
  const { data } = await client.get(`/reality-predict/${constituencyId}/`)
  return data
}

/**
 * Get candidates with details for a constituency.
 * @param {number} constituencyId
 * @returns {Promise<{candidates: Array}>}
 */
export const getCandidates = async (constituencyId) => {
  const { data } = await client.get(`/candidates/${constituencyId}/`)
  return data
}

export default client
