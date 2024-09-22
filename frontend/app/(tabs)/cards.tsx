import axios from 'axios';
import React, { useEffect, useState } from 'react';
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

    const [cardsData, setCardsData] = useState<{ title: string; content: string }[]>([]);

    const colors = ['#C4D6BD', '#F6D7DC', '#ACB8E8'];

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await axios.get('http://10.103.170.182:5000/cards');
                console.log("Cards data:", response.data);
                setCardsData(response.data);
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        };

        fetchData();
        const intervalId = setInterval(fetchData, 2000); // Poll every 5 seconds

        return () => clearInterval(intervalId); // Cleanup interval on component unmount
    }, []);

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