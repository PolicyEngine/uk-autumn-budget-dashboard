import { useState, useEffect, useMemo } from 'react'
import Sidebar from './components/Sidebar'
import Results from './components/Results'
import './App.css'

// Default policy options for UK Autumn Budget analysis
const DEFAULT_POLICIES = [
  {
    id: 'income_tax_threshold',
    name: 'Personal allowance freeze extension',
    description: 'Extend the freeze on income tax thresholds beyond 2028',
    hasParams: true,
    params: {
      extensionYears: { min: 1, max: 5, default: 2, label: 'Extension years' }
    }
  },
  {
    id: 'ni_rates',
    name: 'National Insurance rate changes',
    description: 'Adjust National Insurance contribution rates',
    hasParams: true,
    params: {
      rateChange: { min: -2, max: 2, default: 0.5, step: 0.1, label: 'Rate change (pp)' }
    }
  },
  {
    id: 'vat_standard',
    name: 'VAT rate adjustment',
    description: 'Change the standard rate of VAT',
    hasParams: true,
    params: {
      newRate: { min: 15, max: 25, default: 20, step: 0.5, label: 'New rate (%)' }
    }
  },
  {
    id: 'corp_tax',
    name: 'Corporation tax changes',
    description: 'Adjust the main rate of corporation tax',
    hasParams: true,
    params: {
      newRate: { min: 19, max: 30, default: 25, label: 'New rate (%)' }
    }
  },
  {
    id: 'fuel_duty',
    name: 'Fuel duty changes',
    description: 'End or modify the fuel duty freeze',
    hasParams: true,
    params: {
      increase: { min: 0, max: 10, default: 5, step: 0.5, label: 'Increase (p/litre)' }
    }
  },
  {
    id: 'pension_relief',
    name: 'Pension tax relief reform',
    description: 'Modify the rate of pension contribution tax relief',
    hasParams: true,
    params: {
      reliefRate: { min: 20, max: 40, default: 30, label: 'Relief rate (%)' }
    }
  }
]

function App() {
  const [selectedPolicies, setSelectedPolicies] = useState([])
  const [policyParams, setPolicyParams] = useState({})
  const [results, setResults] = useState(null)
  const [isLoading, setIsLoading] = useState(false)

  // Initialize state from URL on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const policiesParam = params.get('policies')

    if (policiesParam) {
      const policies = policiesParam.split(',')
      setSelectedPolicies(policies)

      // Initialize parameters for selected policies
      const initialParams = {}
      policies.forEach(policyId => {
        const policy = DEFAULT_POLICIES.find(p => p.id === policyId)
        if (policy && policy.hasParams) {
          initialParams[policyId] = {}
          Object.entries(policy.params).forEach(([key, config]) => {
            const urlValue = params.get(`${policyId}_${key}`)
            initialParams[policyId][key] = urlValue ? parseFloat(urlValue) : config.default
          })
        }
      })
      setPolicyParams(initialParams)
    }
  }, [])

  // Update URL when state changes
  useEffect(() => {
    if (selectedPolicies.length === 0) return

    const params = new URLSearchParams()
    params.set('policies', selectedPolicies.join(','))

    // Add policy parameters to URL
    selectedPolicies.forEach(policyId => {
      if (policyParams[policyId]) {
        Object.entries(policyParams[policyId]).forEach(([key, value]) => {
          params.set(`${policyId}_${key}`, value)
        })
      }
    })

    window.history.replaceState({}, '', `?${params.toString()}`)
  }, [selectedPolicies, policyParams])

  // Auto-run analysis when policies or parameters change
  useEffect(() => {
    if (selectedPolicies.length === 0) {
      setResults(null)
      return
    }

    runAnalysis()
  }, [selectedPolicies, policyParams])

  const runAnalysis = async () => {
    setIsLoading(true)

    // Simulate PolicyEngine analysis - replace with actual API call
    // when the budget is announced and PolicyEngine integration is ready
    await new Promise(resolve => setTimeout(resolve, 1000))

    // Mock results data
    const mockResults = {
      policies: selectedPolicies.map(id => {
        const policy = DEFAULT_POLICIES.find(p => p.id === id)
        return {
          id,
          name: policy.name,
          params: policyParams[id] || {}
        }
      }),
      budgetaryImpact: {
        years: [2025, 2026, 2027, 2028, 2029, 2030],
        data: selectedPolicies.map((id, idx) => ({
          policy: DEFAULT_POLICIES.find(p => p.id === id).name,
          values: [2.1 + idx, 2.3 + idx, 2.5 + idx, 2.7 + idx, 2.9 + idx, 3.1 + idx]
        }))
      },
      povertyImpact: {
        absolute: { baseline: 14.2, withPolicies: 13.8 },
        relative: { baseline: 22.1, withPolicies: 21.5 }
      },
      affectedHouseholds: 5200000,
      averageImpact: 425
    }

    setResults(mockResults)
    setIsLoading(false)
  }

  const handlePolicyToggle = (policyId) => {
    setSelectedPolicies(prev => {
      if (prev.includes(policyId)) {
        // Remove policy
        const newParams = { ...policyParams }
        delete newParams[policyId]
        setPolicyParams(newParams)
        return prev.filter(id => id !== policyId)
      } else {
        // Add policy with default parameters
        const policy = DEFAULT_POLICIES.find(p => p.id === policyId)
        if (policy.hasParams) {
          const defaultParams = {}
          Object.entries(policy.params).forEach(([key, config]) => {
            defaultParams[key] = config.default
          })
          setPolicyParams(prev => ({ ...prev, [policyId]: defaultParams }))
        }
        return [...prev, policyId]
      }
    })
  }

  const handleParamChange = (policyId, paramKey, value) => {
    setPolicyParams(prev => ({
      ...prev,
      [policyId]: {
        ...prev[policyId],
        [paramKey]: value
      }
    }))
  }

  return (
    <div className="app">
      <Sidebar
        policies={DEFAULT_POLICIES}
        selectedPolicies={selectedPolicies}
        policyParams={policyParams}
        onPolicyToggle={handlePolicyToggle}
        onParamChange={handleParamChange}
      />

      <main className="main-content">
        <header className="header">
          <div>
            <h1>UK Autumn Budget 2025 dashboard</h1>
          </div>
          {results && (
            <div className="download-buttons-wrapper">
              <button
                className="download-button-header"
                onClick={() => window.dispatchEvent(new CustomEvent('downloadDataTxt'))}
                title="Download as TXT"
                aria-label="Download as TXT"
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="16" y1="13" x2="8" y2="13"></line>
                  <line x1="16" y1="17" x2="8" y2="17"></line>
                  <polyline points="10 9 9 9 8 9"></polyline>
                </svg>
              </button>
              <button
                className="download-button-header"
                onClick={() => window.dispatchEvent(new CustomEvent('downloadDataCsv'))}
                title="Download as CSV"
                aria-label="Download as CSV"
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="8" y1="13" x2="16" y2="13"></line>
                  <line x1="8" y1="17" x2="16" y2="17"></line>
                  <line x1="12" y1="13" x2="12" y2="17"></line>
                </svg>
              </button>
            </div>
          )}
        </header>

        <Results
          results={results}
          isLoading={isLoading}
          selectedPolicies={selectedPolicies}
        />
      </main>
    </div>
  )
}

export default App
