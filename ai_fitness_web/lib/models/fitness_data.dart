class FitnessData {
  final String observation;
  final String dietarySuggestion;
  final String summary;

  FitnessData({
    required this.observation,
    required this.dietarySuggestion,
    required this.summary,
  });

  factory FitnessData.fromJson(Map<String, dynamic> json) {
    return FitnessData(
      observation: json['observation'] ?? '',
      dietarySuggestion: json['dietary_suggestion'] ?? '',
      summary: json['summary'] ?? '',
    );
  }
}
