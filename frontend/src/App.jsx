import React, { useState, useEffect, useRef, useCallback } from 'react'
import './App.css'

const QUICK_STAPLES = [
  { product_id: 24852, product_name: 'Banana' },
  { product_id: 13176, product_name: 'Bag of Organic Bananas' },
  { product_id: 21137, product_name: 'Organic Strawberries' },
  { product_id: 47209, product_name: 'Organic Hass Avocado' },
  { product_id: 21903, product_name: 'Organic Baby Spinach' },
  { product_id: 23909, product_name: '2% Reduced Fat Milk' },
]

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

export default function App() {
  const [basket, setBasket] = useState([
    { product_id: 24852, product_name: 'Banana' },
    { product_id: 23909, product_name: '2% Reduced Fat Milk' },
  ])
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [isSearching, setIsSearching] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)

  const [sampleUsers, setSampleUsers] = useState([])
  const [selectedUser, setSelectedUser] = useState(null)
  const [healthStatus, setHealthStatus] = useState({ status: 'connecting', total_products: 0 })

  const [predictions, setPredictions] = useState([])
  const [isPredicting, setIsPredicting] = useState(false)
  const [predictionError, setPredictionError] = useState(null)

  const searchBoxRef = useRef(null)

  // 1. Initial Load: Diagnostics & Sample Users
  useEffect(() => {
    let isMounted = true

    async function loadInitialData() {
      try {
        const healthRes = await fetch(`${API_BASE}/api/health`)
        if (healthRes.ok && isMounted) {
          const healthData = await healthRes.json()
          setHealthStatus(healthData)
        }
      } catch {
        if (isMounted) {
          setHealthStatus({ status: 'offline', total_products: 0 })
        }
      }

      try {
        const usersRes = await fetch(`${API_BASE}/api/users/sample`)
        if (usersRes.ok && isMounted) {
          const usersData = await usersRes.json()
          setSampleUsers(usersData)
          if (usersData.length > 0) {
            setSelectedUser(usersData[0])
          }
        }
      } catch (err) {
        console.error('Failed to load sample users', err)
      }
    }

    loadInitialData()

    return () => {
      isMounted = false
    }
  }, [])

  // 2. Predict on basket or user change
  const refreshPredictions = useCallback(async (currentBasket, currentUser) => {
    if (currentBasket.length === 0) {
      setPredictions([])
      setPredictionError(null)
      return
    }

    setIsPredicting(true)
    setPredictionError(null)

    try {
      const payload = {
        context_product_ids: currentBasket.map(item => item.product_id),
        user_id: currentUser ? currentUser.user_id : null,
        order_number: currentUser ? currentUser.order_count + 1 : 10,
        top_k: 4,
      }

      const res = await fetch(`${API_BASE}/api/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        throw new Error('Prediction service returned an error')
      }

      const data = await res.json()
      setPredictions(data.predictions || [])
    } catch (err) {
      console.error('Prediction failed', err)
      setPredictionError('Unable to reach prediction engine (it may be cold-starting).')
    } finally {
      setIsPredicting(false)
    }
  }, [])

  useEffect(() => {
    let isCancelled = false

    async function triggerPredictions() {
      if (!isCancelled) {
        await refreshPredictions(basket, selectedUser)
      }
    }

    triggerPredictions()

    return () => {
      isCancelled = true
    }
  }, [basket, selectedUser, refreshPredictions])

  function handleSearchChange(val) {
    setSearchQuery(val)
    if (!val.trim()) {
      setSearchResults([])
      setShowDropdown(false)
    }
  }

  // 3. Search autocomplete debounce
  useEffect(() => {
    const trimmed = searchQuery.trim()
    if (!trimmed) {
      return
    }

    let isCancelled = false

    const timer = setTimeout(async () => {
      if (!isCancelled) {
        setIsSearching(true)
      }
      try {
        const res = await fetch(`${API_BASE}/api/products/search?q=${encodeURIComponent(trimmed)}&limit=8`)
        if (res.ok && !isCancelled) {
          const data = await res.json()
          const currentIds = new Set(basket.map(i => i.product_id))
          const filtered = data.filter(i => !currentIds.has(i.product_id))
          setSearchResults(filtered)
          setShowDropdown(true)
        }
      } catch (err) {
        console.error('Search error', err)
      } finally {
        if (!isCancelled) {
          setIsSearching(false)
        }
      }
    }, 200)

    return () => {
      isCancelled = true
      clearTimeout(timer)
    }
  }, [searchQuery, basket])

  // Click outside listener for search dropdown
  useEffect(() => {
    function handleClickOutside(e) {
      if (searchBoxRef.current && !searchBoxRef.current.contains(e.target)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  function addItem(product) {
    if (basket.some(i => i.product_id === product.product_id)) return
    setBasket(prev => [...prev, product])
    setSearchQuery('')
    setShowDropdown(false)
  }

  function removeItem(productId) {
    setBasket(prev => prev.filter(i => i.product_id !== productId))
  }

  function clearBasket() {
    setBasket([])
  }

  return (
    <div className="app-container">
      {/* Top Navigation */}
      <header className="site-header">
        <div className="header-inner">
          <div className="brand-group">
            <span className="brand-logo" aria-hidden="true">🛒</span>
            <div>
              <h1 className="brand-title">Smart Basket Assistant</h1>
              <p className="brand-subtitle">Explainable Forgotten Item Predictor</p>
            </div>
          </div>

          <div className="header-controls">
            {/* Shopper Persona Switcher */}
            <div className="user-select-box">
              <label htmlFor="user-selector" className="user-label">
                Active Shopper Profile:
              </label>
              <select
                id="user-selector"
                className="user-select"
                value={selectedUser ? selectedUser.user_id : ''}
                onChange={e => {
                  const val = e.target.value
                  if (val === '') {
                    setSelectedUser(null)
                  } else {
                    const u = sampleUsers.find(item => item.user_id === parseInt(val, 10))
                    setSelectedUser(u || null)
                  }
                }}
              >
                <option value="">Guest Shopper (Co-occurrence Only)</option>
                {sampleUsers.map(user => (
                  <option key={user.user_id} value={user.user_id}>
                    User #{user.user_id} ({user.order_count} past orders)
                  </option>
                ))}
              </select>
            </div>

            {/* Health Badge */}
            <div className="health-pill" title="Backend ML Inference Status">
              <span className="pulse-dot" aria-hidden="true"></span>
              <span>
                {healthStatus.status === 'healthy'
                  ? `Engine Live (${healthStatus.total_products?.toLocaleString()} products)`
                  : 'Backend Offline'}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Split-View Grid */}
      <main className="main-content">
        <div className="split-grid">
          {/* Left Column: Basket Editor & Search */}
          <section className="card-box" aria-labelledby="basket-heading">
            <div className="section-header">
              <h2 id="basket-heading" className="section-title">
                Current Shopping Basket
                <span className="badge-count tabular-nums">{basket.length}</span>
              </h2>
              {basket.length > 0 && (
                <button
                  type="button"
                  className="clear-btn"
                  onClick={clearBasket}
                  aria-label="Clear all items from basket"
                >
                  Clear basket
                </button>
              )}
            </div>

            {/* Search Input with Autocomplete */}
            <div className="search-wrapper" ref={searchBoxRef}>
              <div className="search-input-box">
                <svg className="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <circle cx="11" cy="11" r="8"></circle>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
                <input
                  type="search"
                  className="search-input"
                  placeholder="Search & add groceries (e.g., Avocado, Olive Oil, Eggs)…"
                  value={searchQuery}
                  onChange={e => handleSearchChange(e.target.value)}
                  onFocus={() => searchQuery.trim() && setShowDropdown(true)}
                  aria-label="Search grocery products"
                />
                {isSearching && (
                  <span className="search-spinner" aria-label="Searching catalog…" title="Searching catalog…">
                    ⏳
                  </span>
                )}
              </div>

              {/* Autocomplete Dropdown */}
              {showDropdown && searchResults.length > 0 && (
                <ul className="search-dropdown" role="listbox">
                  {searchResults.map(item => (
                    <li
                      key={item.product_id}
                      className="search-dropdown-item"
                      role="option"
                      aria-selected="false"
                      onClick={() => addItem(item)}
                    >
                      <span className="item-name-text">{item.product_name}</span>
                      <span className="item-add-tag">+ Add to cart</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Quick Add Pantry Staples */}
            <div className="quick-chips-section">
              <p className="quick-chips-title">Frequent Pantry Staples:</p>
              <div className="quick-chips-row">
                {QUICK_STAPLES.map(staple => {
                  const inBasket = basket.some(i => i.product_id === staple.product_id)
                  return (
                    <button
                      key={staple.product_id}
                      type="button"
                      className="quick-chip-btn"
                      disabled={inBasket}
                      onClick={() => addItem(staple)}
                      style={{ opacity: inBasket ? 0.45 : 1 }}
                      title={inBasket ? 'Already in basket' : `Add ${staple.product_name}`}
                    >
                      <span>{staple.product_name}</span>
                      <span aria-hidden="true">{inBasket ? '✓' : '+'}</span>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Active Items List */}
            {basket.length === 0 ? (
              <div className="empty-basket-state">
                <svg className="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
                  <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-2z"></path>
                  <line x1="3" y1="6" x2="21" y2="6"></line>
                  <path d="M16 10a4 4 0 0 1-8 0"></path>
                </svg>
                <h3 className="empty-title">Your basket is empty</h3>
                <p className="empty-desc">
                  Add items using the search bar or tap the frequent pantry staples above to see forgotten-item predictions.
                </p>
              </div>
            ) : (
              <ul className="basket-list" aria-label="Shopping items">
                {basket.map(item => (
                  <li key={item.product_id} className="basket-item-row">
                    <div className="basket-item-info">
                      <span className="basket-item-icon" aria-hidden="true">🛒</span>
                      <span className="basket-item-name">{item.product_name}</span>
                    </div>
                    <button
                      type="button"
                      className="remove-btn"
                      onClick={() => removeItem(item.product_id)}
                      aria-label={`Remove ${item.product_name} from basket`}
                      title="Remove item"
                    >
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                      </svg>
                    </button>
                  </li>
                ))}
              </ul>
            )}

            {basket.length > 0 && (
              <div className="basket-footer">
                <span style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
                  Total Items: <strong className="tabular-nums">{basket.length}</strong>
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                  Auto-evaluating basket patterns…
                </span>
              </div>
            )}
          </section>

          {/* Right Column: Predictive Forgotten Items Radar */}
          <section className="card-box radar-panel" aria-labelledby="radar-heading">
            <div className="section-header">
              <h2 id="radar-heading" className="section-title">
                <span aria-hidden="true">💡</span>
                Likely Forgotten Items
              </h2>
              {isPredicting && (
                <span className="badge-count" style={{ background: 'var(--color-amber-bg)', color: 'var(--color-amber-text)' }}>
                  Analyzing…
                </span>
              )}
            </div>

            <p className="radar-header-desc">
              {selectedUser
                ? `Personalized for User #${selectedUser.user_id} using purchase history & association rules.`
                : 'Scored using collective grocery basket association rules.'}
            </p>

            {predictionError && (
              <div className="prediction-error-banner" role="alert" style={{
                background: '#FEF2F2',
                border: '1px solid #FECACA',
                color: '#991B1B',
                padding: '0.75rem 1rem',
                borderRadius: '8px',
                marginBottom: '1rem',
                fontSize: '0.85rem'
              }}>
                {predictionError}
              </div>
            )}

            {/* Live region for accessibility */}
            <div aria-live="polite" className="predictions-container">
              {isPredicting && predictions.length === 0 ? (
                <>
                  <div className="skeleton-card" aria-hidden="true"></div>
                  <div className="skeleton-card" aria-hidden="true"></div>
                </>
              ) : basket.length === 0 ? (
                <div className="empty-basket-state" style={{ padding: '2.5rem 1rem' }}>
                  <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
                    Add at least 1 item to your cart to activate forgotten-item detection.
                  </p>
                </div>
              ) : predictions.length === 0 ? (
                <div className="empty-basket-state">
                  <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
                    No missing staple detected for this basket combination.
                  </p>
                </div>
              ) : (
                predictions.map(pred => (
                  <article key={pred.product_id} className="prediction-card">
                    <div className="prediction-top-row">
                      <h3 className="prediction-item-title">{pred.product_name}</h3>
                      <span className="score-badge tabular-nums">
                        {pred.score > 1 ? `${pred.score.toFixed(1)} score` : `${Math.round(pred.score * 100)}% match`}
                      </span>
                    </div>

                    {/* Explainable Rationale */}
                    <div className="explanation-box">
                      <svg className="spark-icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                        <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" />
                      </svg>
                      <p className="explanation-text">
                        <strong>Why suggested:</strong> {pred.reason}
                      </p>
                    </div>

                    {/* Quick 1-click Add Button */}
                    <button
                      type="button"
                      className="add-suggestion-btn"
                      onClick={() => addItem({ product_id: pred.product_id, product_name: pred.product_name })}
                      aria-label={`Add suggested ${pred.product_name} to cart`}
                    >
                      + Add to Cart
                    </button>
                  </article>
                ))
              )}
            </div>

            {/* Explainability Trust Callout */}
            <div className="science-callout">
              <svg className="callout-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="16" x2="12" y2="12"></line>
                <line x1="12" y1="8" x2="12.01" y2="8"></line>
              </svg>
              <div>
                <p className="callout-title">How Predictions Work</p>
                <p className="callout-desc">
                  Our model analyzes multi-item co-occurrence rules alongside your personal reorder frequency and recency. Every prediction is backed by concrete basket evidence.
                </p>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}
