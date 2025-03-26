import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/fitness_data.dart';

class ApiService {
  final String baseUrl;

  ApiService({this.baseUrl = 'http://localhost:5000/api'});

  Future<FitnessData> askQuestion(String question) async {
    final response = await http.post(
      Uri.parse('$baseUrl/ask'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'question': question}),
    );

    if (response.statusCode == 200) {
      return FitnessData.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to get response: ${response.statusCode}');
    }
  }
}
