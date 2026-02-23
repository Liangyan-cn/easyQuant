import { Typography, Card, Row, Col } from 'antd';
import { LineChartOutlined, FundOutlined, RocketOutlined } from '@ant-design/icons';

const { Title, Paragraph } = Typography;

const Home: React.FC = () => {
  return (
    <div>
      <Title level={2}>欢迎使用 EasyQuant</Title>
      <Paragraph>
        一站式量化交易平台，助您轻松实现投资策略自动化。
      </Paragraph>

      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} sm={12} lg={8}>
          <Card hoverable>
            <LineChartOutlined style={{ fontSize: 32, color: '#1890ff' }} />
            <Title level={4}>策略回测</Title>
            <Paragraph>
              基于历史数据验证您的交易策略，优化参数配置。
            </Paragraph>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card hoverable>
            <FundOutlined style={{ fontSize: 32, color: '#52c41a' }} />
            <Title level={4}>实时行情</Title>
            <Paragraph>
              接入多市场实时数据，把握每一个交易机会。
            </Paragraph>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card hoverable>
            <RocketOutlined style={{ fontSize: 32, color: '#722ed1' }} />
            <Title level={4}>自动交易</Title>
            <Paragraph>
              策略自动执行，7x24小时不间断运行。
            </Paragraph>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Home;
