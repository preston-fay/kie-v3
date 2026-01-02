# KIE v3 Implementation Roadmap

**Document Version**: 1.0
**Date**: 2026-01-02
**Timeline**: 12 weeks to production-ready
**Status**: Planning Complete, Ready to Execute

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Phase Overview](#phase-overview)
3. [Detailed Weekly Plan](#detailed-weekly-plan)
4. [Success Metrics](#success-metrics)
5. [Risk Management](#risk-management)
6. [Team & Resources](#team--resources)

---

## Executive Summary

### Objective

Build KIE v3 as a production-ready, dual-architecture consulting delivery platform with:
- Official Kearney Design System (KDS) integration
- Recharts-based interactive visualizations
- Native geospatial/geocoding capabilities
- 100% feature parity with v2
- Exceptional migration path from v2

### Timeline

**12 weeks** broken into 4 phases:

| Phase | Duration | Focus | Deliverable |
|-------|----------|-------|-------------|
| **Phase 1** | Weeks 1-3 | Foundation | Python backend, KDS integration |
| **Phase 2** | Weeks 4-6 | Visualization | Chart builders, React components |
| **Phase 3** | Weeks 7-9 | Geospatial | Geocoding, mapping, FIPS enrichment |
| **Phase 4** | Weeks 10-12 | Production | Testing, docs, migration tools |

### Critical Path

```
Week 1-2: core_v3 foundation
    ↓
Week 3: KDS brand system
    ↓
Week 4-5: Chart data builders (Python → JSON)
    ↓
Week 6: React/Recharts components
    ↓
Week 7-8: Geocoding system
    ↓
Week 9: Mapping & geospatial
    ↓
Week 10: Integration testing
    ↓
Week 11: Migration tools
    ↓
Week 12: Production readiness
```

---

## Phase Overview

### Phase 1: Foundation (Weeks 1-3)

**Goal**: Establish core_v3 architecture and KDS brand system

**Deliverables**:
- `core_v3/` directory structure
- `web_v3/` React skeleton
- KDS brand system (colors, typography, design tokens)
- FastAPI server with health checks
- Basic data processing pipeline

**Success Criteria**:
- [ ] All core_v3 modules importable
- [ ] FastAPI server runs and responds to `/health`
- [ ] React dev server runs
- [ ] KDS 10-color palette validated
- [ ] No v2 dependencies in v3 code

### Phase 2: Visualization (Weeks 4-6)

**Goal**: Build chart data builders (Python) and Recharts components (React)

**Deliverables**:
- Python chart builders for 25+ chart types
- JSON schema for Recharts configs
- React components wrapping Recharts
- ChartCard and DataCard KDS components
- PowerPoint native chart embedding

**Success Criteria**:
- [ ] Generate Recharts JSON for bar, line, pie, scatter charts
- [ ] React components render from JSON configs
- [ ] No gridlines (enforced)
- [ ] KDS colors applied correctly
- [ ] PowerPoint charts are editable (not images)

### Phase 3: Geospatial (Weeks 7-9)

**Goal**: Implement geocoding, mapping, and FIPS enrichment

**Deliverables**:
- GeocodingPipeline with Nominatim/Census/paid fallback
- Batch geocoding with rate limiting
- FIPS code enrichment
- Interactive maps (Folium, react-leaflet)
- Choropleth, heatmap, marker layers
- GeoJSON/CSV export

**Success Criteria**:
- [ ] Geocode 1000 addresses in <5 minutes
- [ ] >95% success rate with free services
- [ ] FIPS codes assigned correctly
- [ ] Maps render with KDS styling
- [ ] Maps exportable as HTML and PNG

### Phase 4: Production (Weeks 10-12)

**Goal**: Testing, documentation, migration tools, launch prep

**Deliverables**:
- Comprehensive test suite (pytest + React Testing Library)
- Migration tools (spec converter, visual diff, batch migrator)
- Complete documentation (API docs, user guides)
- Brand compliance validator
- Performance benchmarks
- Production deployment scripts

**Success Criteria**:
- [ ] >90% test coverage
- [ ] All migration tools tested on real v2 projects
- [ ] Documentation complete and reviewed
- [ ] Performance meets targets (see Success Metrics)
- [ ] Zero P0/P1 bugs

---

## Detailed Weekly Plan

### Week 1: Core Infrastructure

**Focus**: Set up core_v3 directory structure and base classes

**Tasks**:

1. **Day 1-2: Directory Structure**
   ```bash
   mkdir -p core_v3/{brand,data,charts,slides,geo,insights,export,api,utils}
   mkdir -p core_v3/{brand,data,charts,slides,geo,insights,export,api,utils}/{__init__.py,tests}
   mkdir -p web_v3/src/{components,hooks,lib,types}
   ```

   Files to create:
   - `core_v3/__init__.py` - Package init
   - `core_v3/brand/__init__.py` - Brand system init
   - `core_v3/data/__init__.py` - Data processing init
   - `core_v3/charts/__init__.py` - Chart builders init
   - `core_v3/api/__init__.py` - FastAPI app init
   - `pyproject.toml` - Update with v3 dependencies

2. **Day 3: Base Classes**
   - `core_v3/base.py` - Abstract base classes
   - `core_v3/config.py` - Configuration management
   - `core_v3/exceptions.py` - Custom exceptions

3. **Day 4-5: Data Processing**
   - `core_v3/data/loader.py` - CSV/Excel/JSON loaders
   - `core_v3/data/processor.py` - Pandas/Polars wrapper
   - `core_v3/data/validator.py` - Data quality checks

**Deliverable**: `core_v3/` package structure with base functionality

**Tests**: Unit tests for data loaders and processors

---

### Week 2: FastAPI & React Setup

**Focus**: API server and React frontend skeleton

**Tasks**:

1. **Day 1-2: FastAPI Application**
   - `core_v3/api/main.py` - FastAPI app with CORS
   - `core_v3/api/routes/health.py` - Health check endpoint
   - `core_v3/api/routes/projects.py` - Project CRUD
   - `core_v3/api/routes/charts.py` - Chart generation endpoints
   - `core_v3/api/middleware/` - Logging, error handling

2. **Day 3-4: React Initialization**
   ```bash
   cd web_v3
   npm create vite@latest . -- --template react-ts
   npm install recharts react-leaflet lucide-react
   npm install -D tailwindcss postcss autoprefixer
   ```

   Files to create:
   - `web_v3/src/main.tsx` - React entry point
   - `web_v3/src/App.tsx` - Root component
   - `web_v3/tailwind.config.js` - Tailwind with KDS colors
   - `web_v3/src/lib/api.ts` - FastAPI client

3. **Day 5: Integration Test**
   - Test FastAPI ↔ React communication
   - Verify CORS configuration
   - Test hot reload (both servers)

**Deliverable**: Running FastAPI (port 8000) and React dev server (port 5173)

**Tests**: API endpoint tests, React component smoke tests

---

### Week 3: KDS Brand System

**Focus**: Official KDS integration in Python and React

**Tasks**:

1. **Day 1-2: Python Brand System**
   - `core_v3/brand/colors.py` - KDS 10-color palette
   - `core_v3/brand/typography.py` - Inter font, sizes, weights
   - `core_v3/brand/design_tokens.py` - Spacing, borders, shadows
   - `core_v3/brand/validator.py` - Brand compliance checker
   - `core_v3/brand/forbidden_colors.py` - Green detection

2. **Day 3-4: React KDS Components**
   - Copy from `/Users/pfay01/Projects/Kearney Design System/src/app/components/kearney/`
   - `web_v3/src/components/kds/ChartCard.tsx`
   - `web_v3/src/components/kds/DataCard.tsx`
   - `web_v3/src/components/kds/InsightCard.tsx`
   - `web_v3/src/components/kds/SlideLayout.tsx`

3. **Day 5: Brand Validator**
   - CLI tool: `python -m core_v3.brand.validator <path>`
   - Check color compliance
   - Check typography
   - Check gridlines (must be absent)
   - Generate compliance report

**Deliverable**: Complete KDS brand system with validator

**Tests**: Brand validation tests with positive/negative cases

---

### Week 4: Chart Data Builders (Part 1)

**Focus**: Python classes that generate Recharts JSON configs

**Tasks**:

1. **Day 1: Base Chart Builder**
   - `core_v3/charts/base.py` - Abstract ChartBuilder class
   - `core_v3/charts/schema.py` - JSON schema definitions
   - `core_v3/charts/colors.py` - Color selection logic

2. **Day 2-3: Basic Chart Types**
   - `core_v3/charts/builders/bar.py` - RechartsBarChart
   - `core_v3/charts/builders/line.py` - RechartsLineChart
   - `core_v3/charts/builders/pie.py` - RechartsPieChart
   - `core_v3/charts/builders/scatter.py` - RechartsScatterChart

3. **Day 4-5: Advanced Chart Types**
   - `core_v3/charts/builders/area.py` - RechartsAreaChart
   - `core_v3/charts/builders/combo.py` - RechartsComboChart
   - `core_v3/charts/builders/waterfall.py` - RechartsWaterfallChart
   - `core_v3/charts/builders/bullet.py` - RechartsBulletChart

**Deliverable**: Chart builders that output valid Recharts JSON

**Example Output**:
```json
{
  "type": "bar",
  "data": [
    {"region": "North", "revenue": 1200},
    {"region": "South", "revenue": 980}
  ],
  "config": {
    "xKey": "region",
    "yKeys": ["revenue"],
    "colors": ["#7823DC"],
    "title": "Revenue by Region",
    "axisLine": false,
    "tickLine": false,
    "gridLines": false,
    "dataLabels": {"position": "top", "fontSize": 12}
  }
}
```

**Tests**: Unit tests for each chart type, JSON schema validation

---

### Week 5: Chart Data Builders (Part 2)

**Focus**: Consulting-specific charts and smart defaults

**Tasks**:

1. **Day 1-2: Consulting Charts**
   - `core_v3/charts/builders/gantt.py` - RechartsGanttChart
   - `core_v3/charts/builders/funnel.py` - RechartsFunnelChart
   - `core_v3/charts/builders/matrix.py` - Matrix (2x2, BCG, etc.)
   - `core_v3/charts/builders/treemap.py` - RechartsTreemapChart

2. **Day 3: Smart Defaults**
   - `core_v3/charts/smart_formatting.py` - Auto number formatting (K/M/B)
   - `core_v3/charts/smart_colors.py` - Color selection based on data
   - `core_v3/charts/smart_labels.py` - Label positioning logic

3. **Day 4-5: Chart Factory**
   - `core_v3/charts/factory.py` - ChartFactory.create(chart_type, data, **config)
   - Auto-detect best chart type for data
   - Validation and error handling

**Deliverable**: 25+ chart types with smart defaults

**Tests**: Integration tests with real data, edge cases

---

### Week 6: React Recharts Components

**Focus**: React components that consume JSON configs

**Tasks**:

1. **Day 1-2: Base Components**
   - `web_v3/src/components/charts/BaseChart.tsx` - Wrapper with error handling
   - `web_v3/src/components/charts/BarChart.tsx` - Bar chart component
   - `web_v3/src/components/charts/LineChart.tsx` - Line chart component
   - `web_v3/src/components/charts/PieChart.tsx` - Pie chart component

2. **Day 3-4: Advanced Components**
   - `web_v3/src/components/charts/ComboChart.tsx` - Combo chart
   - `web_v3/src/components/charts/WaterfallChart.tsx` - Waterfall
   - `web_v3/src/components/charts/BulletChart.tsx` - Bullet chart
   - `web_v3/src/components/charts/GanttChart.tsx` - Gantt chart

3. **Day 5: Chart Loader**
   - `web_v3/src/components/charts/ChartLoader.tsx` - Dynamically loads chart from JSON
   - Fetches JSON from FastAPI or local file
   - Type-safe props with TypeScript

**Deliverable**: React components rendering Recharts from JSON

**Example Usage**:
```tsx
import ChartLoader from '@/components/charts/ChartLoader';

<ChartLoader
  configPath="/api/charts/revenue_by_region"
  fallback={<Skeleton />}
/>
```

**Tests**: React Testing Library tests, Storybook stories

---

### Week 7: Geocoding System (Part 1)

**Focus**: Free geocoding services (Nominatim, Census)

**Tasks**:

1. **Day 1: Base Geocoding Classes**
   - `core_v3/geo/base.py` - Abstract Geocoder class
   - `core_v3/geo/models.py` - GeocodingResult dataclass
   - `core_v3/geo/exceptions.py` - Geocoding exceptions

2. **Day 2-3: Nominatim Geocoder**
   - `core_v3/geo/services/nominatim.py` - NominatimGeocoder
   - Rate limiting (1 req/sec for free tier)
   - Retry logic with exponential backoff
   - Confidence scoring

3. **Day 4-5: US Census Geocoder**
   - `core_v3/geo/services/census.py` - CensusGeocoder
   - Batch geocoding (up to 10k addresses)
   - FIPS code extraction
   - Address normalization

**Deliverable**: Working geocoders for Nominatim and Census

**Example Usage**:
```python
from core_v3.geo.services import NominatimGeocoder

geocoder = NominatimGeocoder()
result = await geocoder.geocode(
    address="1600 Amphitheatre Parkway",
    city="Mountain View",
    state="CA"
)
# result.latitude = 37.4224764
# result.longitude = -122.0842499
# result.confidence = 0.95
```

**Tests**: Unit tests with mocked API responses, integration tests with real APIs

---

### Week 8: Geocoding System (Part 2)

**Focus**: Paid services, batch processing, FIPS enrichment

**Tasks**:

1. **Day 1-2: Paid Geocoding Services**
   - `core_v3/geo/services/google.py` - GoogleGeocoder (requires API key)
   - `core_v3/geo/services/mapbox.py` - MapboxGeocoder (requires API key)
   - Environment variable config
   - API key validation

2. **Day 3: Geocoding Pipeline**
   - `core_v3/geo/pipeline.py` - GeocodingPipeline with fallback strategy
   - Try free services first
   - Prompt for API key if confidence < threshold
   - Batch processing with rate limiting

3. **Day 4-5: FIPS Enrichment**
   - `core_v3/geo/fips.py` - FIPS code lookup and enrichment
   - ZIP → FIPS mapping
   - Reverse geocoding (lat/long → FIPS)
   - State/county FIPS codes

**Deliverable**: Production-ready geocoding pipeline

**Example Usage**:
```python
from core_v3.geo import GeocodingPipeline

pipeline = GeocodingPipeline(
    preferred_service='nominatim',
    fallback_services=['census', 'google'],  # Google requires API key
    rate_limit=1.0
)

results = await pipeline.geocode_batch(
    addresses=df['address'].tolist(),
    batch_size=100
)

# Enriches with: latitude, longitude, fips_code, confidence
```

**Tests**: Integration tests with 1000+ address dataset

---

### Week 9: Mapping & Geospatial

**Focus**: Interactive maps with KDS styling

**Tasks**:

1. **Day 1-2: Folium Maps**
   - `core_v3/geo/maps/folium_builder.py` - KDS-styled Folium maps
   - Choropleth layers
   - Marker clusters
   - Heatmaps
   - Custom KDS color scales

2. **Day 3-4: React Leaflet Components**
   - `web_v3/src/components/maps/InteractiveMap.tsx` - react-leaflet wrapper
   - `web_v3/src/components/maps/ChoroplethLayer.tsx` - Choropleth
   - `web_v3/src/components/maps/MarkerCluster.tsx` - Marker clustering
   - `web_v3/src/components/maps/HeatmapLayer.tsx` - Heatmap

3. **Day 5: Map Exports**
   - `core_v3/geo/export/html.py` - Self-contained HTML export
   - `core_v3/geo/export/png.py` - Static PNG for PowerPoint
   - `core_v3/geo/export/geojson.py` - GeoJSON export

**Deliverable**: Interactive maps with KDS branding

**Example Output**:
- `outputs/maps/revenue_by_state.html` - Interactive Folium map
- `outputs/maps/revenue_by_state.png` - Static map for PPTX
- `outputs/maps/revenue_by_state.geojson` - GeoJSON data

**Tests**: Visual regression tests, GeoJSON validation

---

### Week 10: Integration & Testing

**Focus**: End-to-end testing, performance optimization

**Tasks**:

1. **Day 1: End-to-End Test Suite**
   - `tests/e2e/test_full_workflow.py` - Complete KIE v3 workflow
   - Load data → geocode → analyze → visualize → export
   - Test all deliverable types (PPTX, HTML, PDF)

2. **Day 2: Performance Testing**
   - Benchmark geocoding throughput
   - Benchmark chart generation
   - Benchmark React rendering
   - Identify bottlenecks

3. **Day 3-4: Performance Optimization**
   - Implement caching (Redis for geocoding results)
   - Parallelize batch operations
   - Optimize React bundle size
   - Lazy load Recharts components

4. **Day 5: Load Testing**
   - Test FastAPI under load (100 concurrent users)
   - Test geocoding pipeline (10k addresses)
   - Test chart generation (1k charts)

**Deliverable**: Performance benchmarks and optimizations

**Success Criteria**:
- [ ] Geocode 1000 addresses in <5 minutes
- [ ] Generate 100 charts in <10 seconds
- [ ] React bundle size <500KB (gzipped)
- [ ] FastAPI response time <100ms (p95)

**Tests**: Load tests with Locust, performance regression tests

---

### Week 11: Migration Tools

**Focus**: Tools to migrate v2 projects to v3

**Tasks**:

1. **Day 1-2: Spec Migrator**
   - `core_v3/migrate/spec_migrator.py` - Convert spec.yaml (v2) → spec_v3.yaml
   - Handle all project types
   - Validate output schema

2. **Day 3: Visual Diff Tool**
   - `core_v3/migrate/visual_diff.py` - Compare v2 PNG vs v3 Recharts output
   - Side-by-side HTML report
   - Highlight color/layout differences

3. **Day 4: Batch Migrator**
   - `core_v3/migrate/batch_migrator.py` - Migrate multiple projects
   - Parallel processing
   - Error handling and rollback
   - Progress tracking

4. **Day 5: Migration Validation**
   - `core_v3/migrate/validator.py` - Validate migrated projects
   - Check output parity
   - Check brand compliance
   - Generate migration report

**Deliverable**: Complete migration toolset

**Example Usage**:
```bash
# Migrate single project
python -m core_v3.migrate.spec_migrator \
    /path/to/project/spec.yaml \
    /path/to/project/spec_v3.yaml

# Batch migrate
python -m core_v3.migrate.batch_migrator \
    --projects /path/to/projects/ \
    --auto-confirm \
    --parallel 4
```

**Tests**: Test on 10+ real v2 projects

---

### Week 12: Production Readiness

**Focus**: Documentation, deployment, launch prep

**Tasks**:

1. **Day 1: Documentation**
   - API reference (auto-generated from FastAPI)
   - User guide (how to use KIE v3)
   - Developer guide (how to extend KIE v3)
   - Troubleshooting guide

2. **Day 2: Deployment Scripts**
   - `scripts/deploy.sh` - Deploy FastAPI + React
   - Docker configuration (optional)
   - Environment variable setup
   - Health checks

3. **Day 3: Brand Compliance Audit**
   - Run validator on all example outputs
   - Visual inspection of all chart types
   - Verify no green colors anywhere
   - Verify KDS 10-color palette

4. **Day 4: Security Audit**
   - API key management review
   - CORS configuration review
   - Input validation review
   - Dependency vulnerability scan

5. **Day 5: Launch Prep**
   - Final QA pass
   - Update CLAUDE.md with v3 instructions
   - Create `.kie_version` file
   - Tag release: `v3.0.0`

**Deliverable**: Production-ready KIE v3

**Launch Checklist**:
- [ ] All tests passing (>90% coverage)
- [ ] Documentation complete
- [ ] Migration guide reviewed
- [ ] Example projects migrated successfully
- [ ] Performance targets met
- [ ] Security audit complete
- [ ] Zero P0/P1 bugs

---

## Success Metrics

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Geocoding throughput | 1000 addresses in <5 min | Batch test with Nominatim |
| Chart generation | 100 charts in <10 sec | Python benchmark |
| React bundle size | <500KB gzipped | `npm run build` |
| FastAPI response time | <100ms (p95) | Load test with Locust |
| Time to first chart | <3 seconds | E2E test |

### Quality Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test coverage | >90% | pytest-cov |
| Brand compliance | 100% | Automated validator |
| Geocoding success rate | >95% (free services) | Integration test |
| Migration success rate | >95% | Test on 20 v2 projects |
| Documentation completeness | 100% public APIs | Manual review |

### User Experience Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Migration time | <30 minutes per project | User testing |
| Learning curve | <1 hour for v2 users | User testing |
| Perceived speed | "Fast" rating >80% | User survey |
| Error rate | <5% failed operations | Telemetry (if available) |

---

## Risk Management

### High-Risk Items

#### Risk 1: Recharts Performance with Large Datasets

**Likelihood**: Medium
**Impact**: High
**Mitigation**:
- Implement data pagination/windowing
- Add "Render as static PNG" fallback for >10k data points
- Profile and optimize early (Week 6)

#### Risk 2: Geocoding API Rate Limits

**Likelihood**: High
**Impact**: Medium
**Mitigation**:
- Implement aggressive caching (Redis)
- Queue system for batch jobs
- Clear messaging to users about rate limits
- Fallback to paid services with user consent

#### Risk 3: Migration Breaking Changes

**Likelihood**: Low
**Impact**: High
**Mitigation**:
- Keep v2 frozen and available
- Comprehensive migration testing (20+ projects)
- Rollback procedures documented
- User acceptance testing before launch

#### Risk 4: KDS Design Changes

**Likelihood**: Low
**Impact**: Medium
**Mitigation**:
- Pin KDS version in package.json
- Monitor KDS repo for breaking changes
- Abstract KDS tokens into design_tokens.py

### Medium-Risk Items

- **Browser compatibility**: Test on Chrome, Firefox, Safari, Edge (Week 10)
- **API key security**: Audit key storage and transmission (Week 12)
- **Data privacy**: Review geocoding data retention policies (Week 8)
- **Bundle size**: Monitor and optimize React bundle (Week 10)

---

## Team & Resources

### Roles (if expanding team)

| Role | Responsibility | Time Commitment |
|------|----------------|-----------------|
| **Lead Developer** (Claude) | Architecture, coding, testing | Full-time (12 weeks) |
| **Reviewer** (User/Preston) | Code review, QA, UX feedback | Part-time (5 hrs/week) |
| **Design Consultant** | KDS compliance validation | As needed (Week 3, 12) |
| **Test User** | Migration testing, feedback | Week 11-12 |

### Development Environment

**Hardware Requirements**:
- CPU: 4+ cores (for parallel testing)
- RAM: 16GB+ (for large datasets)
- Disk: 10GB free space

**Software Requirements**:
- Python 3.11+
- Node.js 20+
- Git
- Docker (optional, for deployment)

**Services**:
- GitHub (code repository)
- Nominatim (free geocoding)
- US Census Geocoder (free US geocoding)
- Google/Mapbox API keys (optional, for testing paid services)

---

## Weekly Status Reviews

At the end of each week, review:

1. **Completed tasks**: What shipped this week?
2. **Blockers**: What's preventing progress?
3. **Risks**: Any new risks identified?
4. **Adjustments**: Changes to next week's plan?
5. **Demos**: Show working features

**Status Report Template**:
```markdown
# Week N Status Report

## Completed
- [ ] Task 1
- [ ] Task 2

## In Progress
- [ ] Task 3 (80% complete, blocked by X)

## Blockers
- Issue with Y, waiting on Z

## Risks
- Risk A is now high likelihood, mitigation: ...

## Next Week Plan
- Focus on X
- De-prioritize Y (moving to Week N+2)

## Demo
[Link to demo video or screenshots]
```

---

## Launch Criteria

KIE v3 is ready to launch when ALL of these are met:

### Functional Requirements
- [ ] All 25+ chart types generate valid Recharts JSON
- [ ] React components render all chart types
- [ ] Geocoding works with Nominatim, Census, Google, Mapbox
- [ ] Maps render with KDS styling (Folium + react-leaflet)
- [ ] PowerPoint exports with native charts (editable)
- [ ] HTML dashboard exports work
- [ ] FastAPI server stable under load
- [ ] Migration tools convert 20+ v2 projects successfully

### Non-Functional Requirements
- [ ] Performance targets met (see Success Metrics)
- [ ] >90% test coverage
- [ ] 100% brand compliance (automated validation)
- [ ] Documentation complete
- [ ] Security audit passed
- [ ] Zero P0/P1 bugs

### User Acceptance
- [ ] At least 3 real v2 projects migrated by users
- [ ] User feedback incorporated
- [ ] Migration guide validated by users

### Launch Readiness
- [ ] CLAUDE.md updated with v3 instructions
- [ ] `.kie_version` file in KIE repo
- [ ] Git tag `v3.0.0` created
- [ ] Announcement prepared
- [ ] Support plan in place

---

## Post-Launch (Week 13+)

### Week 13-14: Monitoring & Bug Fixes

- Monitor user feedback
- Fix any critical bugs
- Create patch releases (v3.0.1, v3.0.2, etc.)

### Week 15-16: Enhancements

Based on user feedback, prioritize:
- Additional chart types
- New geocoding services
- Performance optimizations
- UX improvements

### Ongoing: v2 → v3 Migration Support

- Assist users with migrations
- Improve migration tools based on real-world usage
- Update migration guide with FAQs

---

## Appendix A: Dependency List

### Python Dependencies (pyproject.toml)

```toml
[project]
name = "kie"
version = "3.0.0"
dependencies = [
    # Core
    "pandas>=2.1.0",
    "polars>=0.19.0",
    "pydantic>=2.0.0",

    # API
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "python-multipart>=0.0.6",

    # Geospatial
    "geopandas>=0.14.0",
    "shapely>=2.0.0",
    "folium>=0.15.0",
    "geopy>=2.4.0",
    "fiona>=1.9.0",

    # Export
    "python-pptx>=0.6.21",
    "openpyxl>=3.1.0",

    # Utils
    "pyyaml>=6.0",
    "requests>=2.31.0",
    "aiohttp>=3.9.0",
    "tenacity>=8.2.0",  # Retry logic
]

[project.optional-dependencies]
geo = [
    "googlemaps>=4.10.0",
    "mapbox>=0.18.0",
]
api = [
    "redis>=5.0.0",
    "celery>=5.3.0",
]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.21.0",
    "mypy>=1.5.0",
    "ruff>=0.1.0",
    "black>=23.9.0",
]
```

### Node.js Dependencies (package.json)

```json
{
  "name": "kie-web-v3",
  "version": "3.0.0",
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "recharts": "^2.15.2",
    "react-leaflet": "^4.2.1",
    "leaflet": "^1.9.4",
    "lucide-react": "^0.294.0",
    "tailwindcss": "^3.3.5",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.37",
    "@types/react-dom": "^18.2.15",
    "@types/leaflet": "^1.9.8",
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0",
    "typescript": "^5.2.2",
    "eslint": "^8.53.0",
    "@testing-library/react": "^14.1.2",
    "vitest": "^1.0.0"
  }
}
```

---

## Appendix B: File Checklist

At launch, these files must exist:

### Core v3 (Python)
- [ ] `core_v3/__init__.py`
- [ ] `core_v3/brand/colors.py`
- [ ] `core_v3/brand/validator.py`
- [ ] `core_v3/charts/builders/` (25+ chart types)
- [ ] `core_v3/geo/pipeline.py`
- [ ] `core_v3/geo/services/` (nominatim, census, google, mapbox)
- [ ] `core_v3/geo/maps/folium_builder.py`
- [ ] `core_v3/api/main.py`
- [ ] `core_v3/migrate/spec_migrator.py`

### Web v3 (React)
- [ ] `web_v3/src/main.tsx`
- [ ] `web_v3/src/components/kds/` (ChartCard, DataCard, etc.)
- [ ] `web_v3/src/components/charts/` (all chart types)
- [ ] `web_v3/src/components/maps/` (map components)
- [ ] `web_v3/package.json`
- [ ] `web_v3/tailwind.config.js`

### Documentation
- [ ] `KIE_V3_ARCHITECTURE.md` ✅ (created)
- [ ] `MIGRATION_V2_TO_V3.md` ✅ (created)
- [ ] `KIE_V3_ROADMAP.md` ✅ (this file)
- [ ] `API_REFERENCE.md`
- [ ] `USER_GUIDE.md`
- [ ] `TROUBLESHOOTING.md`

### Configuration
- [ ] `.kie_version` (contains "v3")
- [ ] `pyproject.toml` (updated with v3 deps)
- [ ] `web_v3/package.json`

### Tests
- [ ] `tests/v3/` (test suite)
- [ ] `tests/v3/test_brand_compliance.py`
- [ ] `tests/v3/test_geocoding.py`
- [ ] `tests/v3/test_chart_builders.py`
- [ ] `tests/v3/test_migration.py`

---

**END OF ROADMAP**

Ready to start implementation? Begin with **Week 1: Core Infrastructure**.

Questions or feedback? Let me know!

---

**Document History**:
- v1.0 (2026-01-02): Initial 12-week roadmap for KIE v3.0.0
