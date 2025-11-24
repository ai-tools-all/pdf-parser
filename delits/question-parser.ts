import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Get the current directory equivalent in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

interface Question = {
  question: string;
  choices: string[];
  answer: string | null;
}

interface QuestionsByTopic = {
  [topic: string]: Question[];
}

function extractTableOfContents(lines: string[]): string[] {
  "Extract table of contents from the text lines."
  const toc: string[] = [];
  let tocStarted = false;
  
  for (const line of lines) {
    const trimmedLine = line.trim();
    if (/^Table of Contents/i.test(trimmedLine)) {
      tocStarted = true;
      continue;
    }
    if (tocStarted && /^\d/.test(trimmedLine)) {
      // End of TOC when we hit a numbered line (questions start)
      break;
    }
    if (tocStarted && trimmedLine) {
      toc.push(trimmedLine);
    }
  }
  
  return toc;
}

function writeTableOfContents(toc: string[], filename: string = 'table_of_contents.txt'): void {
  "Write the table of contents to a file."
  const content = [
    "Table of Contents",
    "=================",
    ...toc.map(item => `- ${item}`)
  ].join('\n');
  
  fs.writeFileSync(filename, content);
}

function extractQuestionsByTopic(lines: string[], toc: string[]): QuestionsByTopic {
  "Extract questions organized by topic."
  const questionsByTopic: QuestionsByTopic = {};
  for (const topic of toc) {
    questionsByTopic[topic] = [];
  }
  
  let currentTopic: string | null = null;
  let currentQuestion: string | null = null;
  let currentChoices: string[] = [];
  
  // Create regex patterns for each topic
  const tocPatterns: { [topic: string]: RegExp } = {};
  for (const topic of toc) {
    tocPatterns[topic] = new RegExp(topic, 'i');
  }
  
  for (const line of lines) {
    const trimmedLine = line.trim();
    
    // Check if this line is a topic heading
    for (const [topic, pattern] of Object.entries(tocPatterns)) {
      if (pattern.test(trimmedLine)) {
        currentTopic = topic;
        break;
      }
    }
    
    // If we found a question number, start a new question
    const questionMatch = trimmedLine.match(/^(\d+)\.(.+)$/);
    if (questionMatch && currentTopic !== null) {
      if (currentQuestion !== null) {
        // Save the previous question
        questionsByTopic[currentTopic].push({
          question: currentQuestion,
          choices: currentChoices,
          answer: null  // Will be filled later
        });
      }
      
      currentQuestion = questionMatch[2].trim();
      currentChoices = [];
    } else if (/^[a-d]\)/.test(trimmedLine)) {
      currentChoices.push(trimmedLine);
    } else if (/^Ans: $\w$/.test(trimmedLine)) {
      // Extract the answer
      const answerMatch = trimmedLine.match(/^Ans: $\w$/);
      const answer = answerMatch ? answerMatch[0] : null;
      
      if (currentQuestion !== null && currentTopic !== null) {
        // Save the question with its answer
        questionsByTopic[currentTopic].push({
          question: currentQuestion,
          choices: currentChoices,
          answer: answer
        });
        currentQuestion = null;
        currentChoices = [];
      }
    }
  }
  
  // Handle the last question if it exists
  if (currentQuestion !== null && currentTopic !== null) {
    questionsByTopic[currentTopic].push({
      question: currentQuestion,
      choices: currentChoices,
      answer: null
    });
  }
  
  return questionsByTopic;
}

function writeQuestionsByTopic(questionsByTopic: QuestionsByTopic, outputDir: string = 'questions'): void {
  "Write questions to separate files by topic."
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir);
  }
  
  for (const [topic, questions] of Object.entries(questionsByTopic)) {
    // Create a filename from the topic
    const filename = topic.replace(/[^\w\-_\. ]/g, '_') + '.txt';
    const filepath = path.join(outputDir, filename);
    
    const content = [
      `Questions about ${topic}`,
      '='.repeat(15 + topic.length),
      ''
    ];
    
    for (let i = 0; i < questions.length; i++) {
      const question = questions[i];
      content.push(`${i + 1}. ${question.question}`);
      
      for (const choice of question.choices) {
        content.push(choice);
      }
      
      if (question.answer) {
        content.push(question.answer);
      }
      
      content.push('');
    }
    
    fs.writeFileSync(filepath, content.join('\n'));
  }
}

function parseTextFile(filename: string): [string[], QuestionsByTopic] {
  "Main function to parse the text file."
  let fileContent = '';
  
  try {
    fileContent = fs.readFileSync(path.join(__dirname, filename), 'utf8');
  } catch (error) {
    console.error(`Error reading file: ${error}`);
    return [[], {}];
  }
  
  // Extract first 100 lines for analysis
  const lines = fileContent.split('\n').slice(0, 100);
  
  // Extract table of contents
  const toc = extractTableOfContents(lines);
  
  // Write table of contents to file
  writeTableOfContents(toc);
  
  // Extract questions by topic
  const questionsByTopic = extractQuestionsByTopic(lines, toc);
  
  // Write questions to files
  writeQuestionsByTopic(questionsByTopic);
  
  return [toc, questionsByTopic];
}

// Example usage with a sample file
const [toc, questions] = parseTextFile("sample.txt");

console.log("Table of Contents:");
for (const item of toc) {
  console.log(`- ${item}`);
}

console.log("\nQuestions by Topic:");
for (const [topic, qList] of Object.entries(questions)) {
  console.log(`\n${topic} (${qList.length} questions):`);
  for (let i = 0; i < qList.length; i++) {
    const q = qList[i];
    console.log(`${i + 1}. ${q.question}`);
    console.log(`   Choices: ${q.choices}`);
    console.log(`   Answer: ${q.answer}`);
  }
}
