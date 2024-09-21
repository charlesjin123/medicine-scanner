import React from 'react';
import { View, ScrollView, StyleSheet, Text } from 'react-native';

const Card: React.FC<{ title: string; content: string, backgroundColor: string }> = ({ title, content, backgroundColor }) => {
    return (
        <View style={[cardStyles.card, { backgroundColor }]}>
            <Text style={cardStyles.title}>{title}</Text>
            <Text style={cardStyles.content}>{content}</Text>
        </View>
    );
};

const CardsScreen: React.FC = () => {
    const cardsData = [
        { title: 'Card 1', content: 'This is the content of card 1.' },
        { title: 'Aspirin - 25mg', content: 'Drink a Full Glass of Water with Each Dose' },
        { title: 'Card 3', content: 'This is the content of card 3.' },
        // Add more cards as needed
    ];

    const colors = ['#C4D6BD', '#F6D7DC', '#ACB8E8'];

    return (
        <View style={styles.container}>
            <ScrollView contentContainerStyle={styles.cardContainer}>
                {cardsData.map((card, index) => (
                    <Card key={index} title={card.title} content={card.content} backgroundColor={colors[index % colors.length]} />
                ))}
            </ScrollView>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#FDDBB7',
    },
    cardContainer: {
        paddingVertical: 16,
        paddingHorizontal: 8,
    },
});

const cardStyles = StyleSheet.create({
    card: {
        backgroundColor: '#f9f9f9',
        borderRadius: 15,
        padding: 16,
        marginVertical: 16,
        marginHorizontal: 16,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
        elevation: 2,
        height: 600, // Increase the height of the cards
        justifyContent: 'center', // Center content vertically
    },
    title: {
        fontSize: 25, // Make the title smaller
        fontWeight: 'bold',
        position: 'absolute', // Position the title absolutely
        top: 15, // Position it at the top
        left: 15, // Position it at the left
    },
    content: {
        fontSize: 24, // Big center text content
        textAlign: 'center', // Center the text horizontally
    },
});

export default CardsScreen;