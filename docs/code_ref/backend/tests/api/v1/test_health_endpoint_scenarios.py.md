---
sidebar_label: test_health_endpoint_scenarios
---

## client()

```python
def client():
```

## test_health_all_components_healthy()

```python
def test_health_all_components_healthy(monkeypatch, client):
```

## test_health_degraded_when_component_degraded()

```python
def test_health_degraded_when_component_degraded(monkeypatch, client):
```

## test_health_endpoint_graceful_failure()

```python
def test_health_endpoint_graceful_failure(monkeypatch, client):
```

## test_health_endpoint_failed_components()

```python
def test_health_endpoint_failed_components(monkeypatch, client):
```

When components fail (unhealthy), endpoint should not 500 and should degrade.
