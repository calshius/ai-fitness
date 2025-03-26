import 'package:flutter/material.dart';
import '../models/fitness_data.dart';

class FitnessCard extends StatelessWidget {
  final FitnessData data;

  const FitnessCard({Key? key, required this.data}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8.0),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Observations',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            Text(data.observation),
            const Divider(),
            Text(
              'Dietary Suggestions',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            Text(data.dietarySuggestion),
            const Divider(),
            Text(
              'Summary',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            Text(data.summary),
          ],
        ),
      ),
    );
  }
}
