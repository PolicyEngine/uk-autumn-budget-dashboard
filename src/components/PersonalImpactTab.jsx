import "./PersonalImpactTab.css";

const LIFECYCLE_URL = "https://uk-autumn-budget-lifecycle.vercel.app/";

function PersonalImpactTab() {
  return (
    <div className="personal-impact-tab">
      <div className="lifecycle-iframe-container">
        <iframe
          src={LIFECYCLE_URL}
          title="Lifecycle impact calculator"
          className="lifecycle-iframe"
          allow="clipboard-write"
        />
      </div>
    </div>
  );
}

export default PersonalImpactTab;
