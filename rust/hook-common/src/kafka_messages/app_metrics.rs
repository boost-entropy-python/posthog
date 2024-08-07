use chrono::{DateTime, Utc};
use serde::{Deserialize, Deserializer, Serialize, Serializer};
use uuid::Uuid;

use super::{deserialize_datetime, serialize_datetime};

#[derive(Deserialize, Serialize, Debug, PartialEq, Clone)]
pub enum AppMetricCategory {
    ProcessEvent,
    OnEvent,
    ScheduledTask,
    Webhook,
    ComposeWebhook,
}

// NOTE: These are stored in Postgres and deserialized by the cleanup/janitor process, so these
// names need to remain stable, or new variants need to be deployed to the cleanup/janitor
// process before they are used.
#[derive(Deserialize, Serialize, Debug, PartialEq, Clone)]
#[serde(try_from = "String", into = "String")]
pub enum ErrorType {
    TimeoutError,
    ConnectionError,
    BadHttpStatus(u16),
    ParseError,
}

// NOTE: This is stored in Postgres and deserialized by the cleanup/janitor process, so this
// shouldn't change. It is intended to replicate the shape of `error_details` used in the
// plugin-server and by the frontend.
#[derive(Deserialize, Serialize, Debug, PartialEq, Clone)]
pub struct ErrorDetails {
    pub error: Error,
}

#[derive(Deserialize, Serialize, Debug, PartialEq, Clone)]
pub struct Error {
    pub name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub message: Option<String>,
    // This field will only be useful if we start running plugins in Rust (via a WASM runtime or
    // something) and want to provide the user with stack traces like we do for TypeScript plugins.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub stack: Option<String>,
}

#[derive(Deserialize, Serialize, Debug, PartialEq, Clone)]
pub struct AppMetric {
    #[serde(
        serialize_with = "serialize_datetime",
        deserialize_with = "deserialize_datetime"
    )]
    pub timestamp: DateTime<Utc>,
    pub team_id: u32,
    pub plugin_config_id: i32,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub job_id: Option<String>,
    #[serde(
        serialize_with = "serialize_category",
        deserialize_with = "deserialize_category"
    )]
    pub category: AppMetricCategory,
    pub successes: u32,
    pub successes_on_retry: u32,
    pub failures: u32,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error_uuid: Option<Uuid>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub error_type: Option<ErrorType>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error_details: Option<ErrorDetails>,
}

fn serialize_category<S>(category: &AppMetricCategory, serializer: S) -> Result<S::Ok, S::Error>
where
    S: Serializer,
{
    let category_str = match category {
        AppMetricCategory::ProcessEvent => "processEvent",
        AppMetricCategory::OnEvent => "onEvent",
        AppMetricCategory::ScheduledTask => "scheduledTask",
        AppMetricCategory::Webhook => "webhook",
        AppMetricCategory::ComposeWebhook => "composeWebhook",
    };
    serializer.serialize_str(category_str)
}

fn deserialize_category<'de, D>(deserializer: D) -> Result<AppMetricCategory, D::Error>
where
    D: Deserializer<'de>,
{
    let s: String = Deserialize::deserialize(deserializer)?;

    let category = match &s[..] {
        "processEvent" => AppMetricCategory::ProcessEvent,
        "onEvent" => AppMetricCategory::OnEvent,
        "scheduledTask" => AppMetricCategory::ScheduledTask,
        "webhook" => AppMetricCategory::Webhook,
        "composeWebhook" => AppMetricCategory::ComposeWebhook,
        _ => {
            return Err(serde::de::Error::unknown_variant(
                &s,
                &[
                    "processEvent",
                    "onEvent",
                    "scheduledTask",
                    "webhook",
                    "composeWebhook",
                ],
            ))
        }
    };

    Ok(category)
}

impl TryFrom<String> for ErrorType {
    type Error = String;

    fn try_from(s: String) -> Result<Self, Self::Error> {
        match s.as_str() {
            "Connection Error" | "ConnectionError" => Ok(ErrorType::ConnectionError),
            "Timeout Error" | "TimeoutError" => Ok(ErrorType::TimeoutError),
            s if s.starts_with("Bad HTTP Status:") => {
                let status = &s["Bad HTTP Status:".len()..].trim();
                let parsed_status = status
                    .parse::<u16>()
                    .map_err(|e| format!("Failed to parse HTTP status: {}", e))?;
                Ok(ErrorType::BadHttpStatus(parsed_status))
            }
            "Parse Error" | "ParseError" => Ok(ErrorType::ParseError),
            _ => Err(format!("Unknown ErrorType: {}", s)),
        }
    }
}

impl From<ErrorType> for String {
    fn from(error: ErrorType) -> Self {
        match error {
            ErrorType::ConnectionError => "Connection Error".to_string(),
            ErrorType::TimeoutError => "Timeout Error".to_string(),
            ErrorType::BadHttpStatus(s) => format!("Bad HTTP Status: {}", s),
            ErrorType::ParseError => "Parse Error".to_string(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_app_metric_serialization() {
        use chrono::prelude::*;

        let app_metric = AppMetric {
            timestamp: Utc.with_ymd_and_hms(2023, 12, 14, 12, 2, 0).unwrap(),
            team_id: 123,
            plugin_config_id: 456,
            job_id: None,
            category: AppMetricCategory::Webhook,
            successes: 10,
            successes_on_retry: 0,
            failures: 2,
            error_uuid: Some(Uuid::parse_str("550e8400-e29b-41d4-a716-446655447777").unwrap()),
            error_type: Some(ErrorType::ConnectionError),
            error_details: Some(ErrorDetails {
                error: Error {
                    name: "FooError".to_owned(),
                    message: Some("Error Message".to_owned()),
                    stack: None,
                },
            }),
        };

        let serialized_json = serde_json::to_string(&app_metric).unwrap();

        let expected_json = r#"{"timestamp":"2023-12-14 12:02:00","team_id":123,"plugin_config_id":456,"category":"webhook","successes":10,"successes_on_retry":0,"failures":2,"error_uuid":"550e8400-e29b-41d4-a716-446655447777","error_type":"Connection Error","error_details":{"error":{"name":"FooError","message":"Error Message"}}}"#;

        assert_eq!(serialized_json, expected_json);
    }
}
